"""
One-time initialisation of

•   the SQLite database (populated from data/df_total.csv if missing)
•   two ChatOpenAI models that talk to the **GapGPT** endpoint
•   a LangChain SQL-agent that turns NL queries into SQL
•   helper to answer a query and (optionally) create a bar-chart

This is imported by the Telegram command handler – there is no per-request
overhead; everything heavy is done at module import.
"""
from __future__ import annotations
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
import openai
from openai.error import RateLimitError
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit, create_sql_agent
from langchain_openai import ChatOpenAI
import matplotlib.pyplot as plt

from config import config  # our new config module

# ----------------------------------------------------------------- OpenAI cfg
openai.api_key  = config.GAPGPT_API_KEY
openai.api_base = config.GAPGPT_API_BASE          # 🔑 << GapGPT lives here

# ----------------------------------------------------------------- database
DATA_DIR   = Path(__file__).resolve().parents[1] / "data"
CSV_PATH   = DATA_DIR / "dftotal.csv"             # note: filename in repo = dftotal.csv
SQLITE_PATH = DATA_DIR / "df_total.db"
engine     = create_engine(f"sqlite:///{SQLITE_PATH}", echo=False)

if CSV_PATH.exists() and not SQLITE_PATH.exists():
    df = pd.read_csv(CSV_PATH)
    df.to_sql("df_total", con=engine, if_exists="replace", index=False)

db = SQLDatabase.from_uri(f"sqlite:///{SQLITE_PATH}")

# ----------------------------------------------------------------- LLMs
_llm_args = dict(base_url=config.GAPGPT_API_BASE,
                 openai_api_key=config.GAPGPT_API_KEY,
                 temperature=0)

llm_primary  = ChatOpenAI(model="gpt-4o-mini",  **_llm_args)
llm_fallback = ChatOpenAI(model="gpt-3.5-turbo", **_llm_args)

agent_primary  = create_sql_agent(
    llm=llm_primary,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm_primary),
    verbose=True,
    agent_type="openai-functions",
)
agent_fallback = create_sql_agent(
    llm=llm_fallback,
    toolkit=SQLDatabaseToolkit(db=db, llm=llm_fallback),
    verbose=False,
    agent_type="openai-functions",
)

# ----------------------------------------------------------------- helpers
@retry(retry=retry_if_exception_type(RateLimitError),
       wait=wait_exponential(multiplier=1, max=4),
       stop=stop_after_attempt(3),
       reraise=True)
def _invoke(agent, question: str) -> str:
    """
    Wrapper around LangChain agent with automatic retry on RateLimitError.
    Returns **text** – agent always puts final answer into result["output"].
    """
    return agent({"input": question})["output"]


def _plot_bar(df: pd.DataFrame, title: str, fname: str) -> Path:
    """Simple bar plot helper; returns path to saved PNG."""
    plt.figure()
    plt.bar(df.iloc[:, 0].astype(str), df.iloc[:, 1])
    plt.title(title)
    plt.tight_layout()
    out = DATA_DIR / fname
    plt.savefig(out)
    plt.close()
    return out


# ----------------------------------------------------------------- public API
def answer_query(question: str) -> tuple[str, Path | None]:
    """
    Main entry point for the Telegram handler.

    Returns
    -------
    text : str   – reply to send with `reply_text`
    plot : Path? – if not None, send via `reply_photo`
    """
    q = question.lower().strip()

    # ----------- trivial shortcut: "how many rows?"
    if any(k in q for k in ("how many rows", "row count")):
        with engine.connect() as conn:
            n = conn.execute(text("SELECT COUNT(*) FROM df_total")).scalar()
        return f"The dataset has **{n}** rows.", None

    # ----------- built-in chart: gender distribution
    if "plot" in q and "gender" in q:
        df = pd.read_sql("SELECT gender, COUNT(*) AS cnt FROM df_total GROUP BY gender", engine)
        img = _plot_bar(df, "Gender distribution", "gender_dist.png")
        txt = ", ".join(f"{row.gender}: {row.cnt}" for row in df.itertuples())
        return f"Gender distribution → {txt}", img

    # ----------- agent fallback
    try:
        reply = _invoke(agent_primary, question)
        return reply, None
    except RateLimitError:
        try:
            reply = _invoke(agent_fallback, question)
            return reply, None
        except RateLimitError:
            return ("⚠️ Both GapGPT models hit rate-limits; try again later.", None)
    except Exception as exc:
        return (f"❌ Unexpected error: {exc}", None)
