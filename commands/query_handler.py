import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import matplotlib.pyplot as plt  # Importing matplotlib for plotting

# --- OpenAI (compatible with GapGPT) --------------------
from openai import OpenAI, RateLimitError            # openai ≥1.0
# ------------------------------------------------------

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import (
    SQLDatabaseToolkit,
    create_sql_agent,
)
from langchain_openai import ChatOpenAI
# ------------------------------------------------------

# 1) Load the API key from .env file
load_dotenv()                             # Ensure that .env contains the field GAPGPT_API_KEY
GAPGPT_KEY  = os.getenv("GAPGPT_API_KEY")  # Do not hardcode the key in the code!

# 2) Initialize the base client (for direct calls to OpenAI methods if needed)
client = OpenAI(
    api_key = GAPGPT_KEY,
    base_url = "https://api.gapgpt.app/v1"   # GapGPT service endpoint URL
)

# 3) Prepare the SQLite database from the CSV file
DB_PATH = "data/df_total.db"
engine   = create_engine(f"sqlite:///{DB_PATH}", echo=False)

df = pd.read_csv("data/df_total.csv")
df.to_sql("df_total", con=engine, if_exists="replace", index=False)

# 4) Wrap the DB for LangChain usage
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

# 5) Define two LLMs (primary and fallback) for GapGPT
common_llm_args = dict(
    base_url        = "https://api.gapgpt.app/v1",
    openai_api_key  = GAPGPT_KEY,
    temperature     = 0,
)

llm_primary  = ChatOpenAI(model="gpt-4o-mini", **common_llm_args)
llm_fallback = ChatOpenAI(model="gpt-3.5-turbo", **common_llm_args)

# 6) Create the SQL agents using LangChain
toolkit_primary  = SQLDatabaseToolkit(db=db, llm=llm_primary)
agent_primary    = create_sql_agent(
    llm        = llm_primary,
    toolkit    = toolkit_primary,
    verbose    = True,
    agent_type = "openai-tools"
)

toolkit_fallback = SQLDatabaseToolkit(db=db, llm=llm_fallback)
agent_fallback   = create_sql_agent(
    llm        = llm_fallback,
    toolkit    = toolkit_fallback,
    verbose    = False,
    agent_type = "openai-tools"
)

# 7) Retry wrapper for RateLimitError using tenacity library
@retry(
    retry = retry_if_exception_type(RateLimitError),
    wait  = wait_exponential(multiplier=1, max=4),
    stop  = stop_after_attempt(3),
)
def invoke_agent(agent, query: str) -> str:
    """Invoke a LangChain SQL-agent and return only its textual output."""
    result = agent.invoke({"input": query})
    return result["output"]

# Function to check the type of query result
def check_query_result_type(query_result):
    """Check the type of the query result and return an appropriate message or handle accordingly."""
    if isinstance(query_result, pd.DataFrame):  # If it's a DataFrame
        return "DataFrame"
    elif isinstance(query_result, tuple):  # If it's a tuple (e.g., result of a SELECT query)
        return "Tuple"
    elif isinstance(query_result, list):  # If it's a list
        return "List"
    elif isinstance(query_result, str):  # If it's a string (e.g., error message)
        return "String"
    else:
        return "Unknown Type"

# Function to generate and display a plot based on query results
def generate_plot(query_result):
    # Assume query_result is a DataFrame, if not, adjust accordingly.
    # Here, let's plot the first two columns as a bar chart.
    
    result_type = check_query_result_type(query_result)
    
    if result_type == "DataFrame":
        query_result.plot(kind='bar')  # You can modify the plot type (line, scatter, etc.)
        plt.title("Query Result Plot")
        plt.xlabel("Index")
        plt.ylabel("Values")
        plt.show()  # Display the plot
    elif result_type == "Tuple" or result_type == "List":
        # Handle Tuple or List results, perhaps by converting to DataFrame or another plot-friendly format
        print(f"Result is of type: {result_type}, but cannot be plotted directly.")
    elif result_type == "String":
        print(f"Result is a string: {query_result}")  # Log or handle string results
    else:
        print("Result type is unknown and cannot be handled.")

# 8) User query handler
def handle_query(user_query: str) -> str:
    q_lower = user_query.lower()

    # Handling simple row count queries
    if any(kw in q_lower for kw in ("how many rows", "row count", "number of rows")):
        try:
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM df_total")).scalar()
            return f"There are {count} rows in the dataset."
        except Exception as e:
            return f"❌ Error counting rows: {e}"

    # Clarifying gender-related queries
    if "how many man" in q_lower or "how many men" in q_lower:
        user_query = (
            "How many male individuals are in the dataset? "
            "Please count rows where the gender/sex column indicates male."
        )

    # Attempting the primary model and fallback if rate-limited
    try:
        query_result = invoke_agent(agent_primary, user_query)
        # After getting the query result, try to plot it
        generate_plot(query_result)  # This will generate the plot if the result is suitable
        return query_result
    except RateLimitError:
        try:
            query_result = invoke_agent(agent_fallback, user_query)
            generate_plot(query_result)  # Plot fallback results
            return query_result
        except RateLimitError:
            return (
                "⚠️ Rate limits reached on both GapGPT models. "
                "Please check your quota and try again later."
            )
    except Exception as e:
        return f"❌ An unexpected error occurred: {e}"
