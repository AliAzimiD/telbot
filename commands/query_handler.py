"""
Agent-powered SQL-Q&A روی SQLite با استفاده از GapGPT
====================================================
پیش‌نیازها:
  pip install openai langchain-openai langchain-community sqlalchemy python-dotenv tenacity pandas
"""

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# --- OpenAI (سازگار با GapGPT) --------------------
from openai import OpenAI, RateLimitError            # openai ≥1.0
# --------------------------------------------------

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from langchain_community.utilities import SQLDatabase

from langchain_community.agent_toolkits import (
    SQLDatabaseToolkit,
    create_sql_agent,
)
from langchain_openai import ChatOpenAI
# --------------------------------------------------

# 1) بارگذاری کلید در env
load_dotenv()                             # .env باید فیلدی با نام  GAPGPT_API_KEY  داشته باشد
GAPGPT_KEY  = os.getenv("GAPGPT_API_KEY")  # کلید را مستقیماً در کد ننویسید!

# 2) کلاینت پایه (در صورت نیاز مستقیم به متدهای OpenAI)
client = OpenAI(
    api_key = GAPGPT_KEY,
    base_url = "https://api.gapgpt.app/v1"   # آدرس End-Point سرویس GapGPT
)

# 3) آماده‌سازی پایگاه داده SQLite از فایل CSV
DB_PATH = "data/df_total.db"
engine   = create_engine(f"sqlite:///{DB_PATH}", echo=False)

df = pd.read_csv("data/df_total.csv")
df.to_sql("df_total", con=engine, if_exists="replace", index=False)

# 4)‌ کپسوله‌سازی DB برای LangChain
db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

# 5) تعریف دو LLM (اصلی و پشتیبان) روی GapGPT
common_llm_args = dict(
    base_url        = "https://api.gapgpt.app/v1",
    openai_api_key  = GAPGPT_KEY,
    temperature     = 0,
)

llm_primary  = ChatOpenAI(model="gpt-4o-mini", **common_llm_args)
llm_fallback = ChatOpenAI(model="gpt-3.5-turbo", **common_llm_args)

# 6) ساخت Agentها
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

# 7) رَپِرِ فراخوان با Retry (روی RateLimitError)
@retry(
    retry = retry_if_exception_type(RateLimitError),
    wait  = wait_exponential(multiplier=1, max=4),
    stop  = stop_after_attempt(3),
)
def invoke_agent(agent, query: str) -> str:
    """Invoke a LangChain SQL-agent and return only its textual output."""
    result = agent.invoke({"input": query})
    return result["output"]

# 8) هندلر پرسش کاربر
def handle_query(user_query: str) -> str:
    q_lower = user_query.lower()

    # پرسش‌های ساده شمارش ردیف
    if any(kw in q_lower for kw in ("how many rows", "row count", "number of rows")):
        try:
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM df_total")).scalar()
            return f"There are {count} rows in the dataset."
        except Exception as e:
            return f"❌ Error counting rows: {e}"

    # واضح‌سازی پرسش درباره جنسیت
    if "how many man" in q_lower or "how many men" in q_lower:
        user_query = (
            "How many male individuals are in the dataset? "
            "Please count rows where the gender/sex column indicates male."
        )

    # تلاش با مدل اصلی و در صورت لزوم پشتیبان
    try:
        return invoke_agent(agent_primary, user_query)
    except RateLimitError:
        try:
            return invoke_agent(agent_fallback, user_query)
        except RateLimitError:
            return (
                "⚠️ Rate limits reached on both GapGPT models. "
                "Please check your quota and try again later."
            )
    except Exception as e:
        return f"❌ An unexpected error occurred: {e}"
