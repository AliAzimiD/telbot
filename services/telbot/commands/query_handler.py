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
# Function to invoke the LangChain SQL-agent and explore the full response
def invoke_agent(agent, query: str) -> str:
    """Invoke a LangChain SQL-agent and return detailed result."""
    # Send the query to the agent and get the full response
    result = agent.invoke({"input": query})

    # Print the full result to explore its structure and find other useful keys
    print("Full response from agent:", result)

    # Check if the response has an "output" key, and if so, return it
    if "output" in result:
        return result["output"]
    else:
        # If "output" is not found, return the entire response for inspection
        return str(result)

# Function to generate and display a plot based on query results
def generate_plot(query_result):
    """
    This function takes the query result (assumed to be a DataFrame) and generates a plot.
    It saves the plot as a PNG file to be sent to the user.
    """
    if isinstance(query_result, pd.DataFrame):
        query_result.plot(kind='bar')  # Modify plot type as needed
        plt.title("Query Result Plot")
        plt.xlabel("Index")
        plt.ylabel("Values")
        
        # Save the plot as an image file
        plot_filename = "query_result_plot.png"
        plt.savefig(plot_filename)  # Save the plot as a PNG file
        plt.close()  # Close the plot to avoid showing it interactively
        
        # Return the plot filename for sending to the user
        return plot_filename
    else:
        print("The query result is not a DataFrame, unable to generate plot.")
        return None

# Function to convert natural language to SQL using OpenAI LLM
def convert_to_sql(query: str) -> str:
    """
    This function takes a natural language query and uses basic pattern matching 
    to convert it into a valid SQL query. This can be extended with more complex patterns.
    """
    
    # Check for a query about education levels distribution
    if "distribution of education levels" in query.lower():
        return """
        SELECT Educations, COUNT(*) as count
        FROM df_total
        GROUP BY Educations;
        """
    
    # Check for a query about employed vs. non-employed individuals
    elif "currently employed" in query.lower() and "have left" in query.lower():
        return """
        SELECT isactive, COUNT(*) 
        FROM df_total 
        GROUP BY isactive;
        """
    
    # Handle other queries (e.g., count rows, count males, etc.)
    elif "how many rows" in query.lower() or "row count" in query.lower():
        return "SELECT COUNT(*) FROM df_total;"
    
    # Fallback: If no recognized query, return a generic one
    else:
        return "SELECT * FROM df_total LIMIT 10;"

# 8) User query handler
def handle_query(user_query: str) -> str:
    q_lower = user_query.lower()

    # Convert the natural language query to SQL using basic pattern matching
    sql_query = convert_to_sql(user_query)

    # Execute the SQL query and return the result as a DataFrame
    try:
        query_result = pd.read_sql_query(sql_query, engine)
        
        # After getting the query result, generate a plot
        plot_filename = generate_plot(query_result)  # Save the plot and get the filename
        return f"Query result plot saved as {plot_filename}. Please check the file."
    
    except RateLimitError:
        try:
            query_result = invoke_agent(agent_fallback, user_query)
            
            # If the result is a string, convert it to a DataFrame
            if isinstance(query_result, str):
                query_result = 0
            
            plot_filename = generate_plot(query_result)  # Plot fallback results
            return f"Query result plot saved as {plot_filename}. Please check the file."
        except RateLimitError:
            return (
                "⚠️ Rate limits reached on both GapGPT models. "
                "Please check your quota and try again later."
            )
    except Exception as e:
        return f"❌ An unexpected error occurred: {e}"
