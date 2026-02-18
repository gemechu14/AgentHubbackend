import os
import re
from dotenv import load_dotenv

from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

# -----------------------------
# Load env
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
DB_URI = os.environ["SMARTSCHEMA_DB_URI"]

# -----------------------------
# Database
# -----------------------------
db = SQLDatabase.from_uri(DB_URI)

# -----------------------------
# LLM (same role as article)
# -----------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",   # fast + cheap
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
)

# -----------------------------
# SQL generation chain
# -----------------------------
sql_prompt = ChatPromptTemplate.from_template(
    """Based on the table schema below, write a SQL query that would answer the user's question.

Schema:
{schema}

Question:
{question}

SQL Query:"""
)

def get_schema(_):
    return db.get_table_info()

sql_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | sql_prompt
    | llm.bind(stop=["\nSQLResult:"])
    | StrOutputParser()
)

# -----------------------------
# Final answer chain
# -----------------------------
answer_prompt = ChatPromptTemplate.from_template(
    """Based on the table schema, the question, the SQL query, and the SQL response,
write a natural language answer.

Schema:
{schema}

Question:
{question}

SQL Query:
{query}

SQL Response:
{response}

Answer:"""
)

def _extract_sql_from_text(text: str) -> str | None:
    # First, try to find a fenced code block with optional "sql" hint
    m = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.S | re.I)
    if m:
        return m.group(1).strip()

    # Otherwise, try to find the first SQL statement starting with a common SQL keyword
    m = re.search(r"(?i)(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b.*", text, re.S)
    if m:
        return text[m.start():].strip()

    return None


def run_query(query_or_text):
    """Extract SQL from model output and execute it. If no SQL is found,
    return the original text (so the answer chain can use it as a message).
    """
    sql = _extract_sql_from_text(query_or_text)
    if not sql:
        # Nothing executable detected — return the model output unchanged
        return query_or_text

    try:
        # Print the SQL statement that will be executed for visibility/debugging
        print("\n--- Executing SQL ---")
        print(sql)
        print("--- End SQL ---\n")

        result = db.run(sql)
        return str(result)
    except Exception as e:
        # Return a clear error message instead of raising, so the answer prompt can include it
        return f"SQL execution error: {e}\n\nOriginal SQL:\n{sql}"

full_chain = (
    RunnablePassthrough.assign(query=sql_chain).assign(
        schema=get_schema,
        response=lambda vars: run_query(vars["query"]),
    )
    | answer_prompt
    | llm
)

# -----------------------------
# Interactive loop
# -----------------------------
print("Connected to SmartSchema DB")
print("Ask a question (type 'exit' to quit)\n")

while True:
    question = input("You: ").strip()
    if question.lower() in {"exit", "quit"}:
        break

    answer = full_chain.invoke({"question": question})
    print("\nAI:")
    print(answer.content)
    print("\n" + "-" * 60 + "\n")
