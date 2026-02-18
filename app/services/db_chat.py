"""
DB Chat Service - Implements chat-on-data functionality for SQL databases
Based on chat_db_open_ai.py
"""
import re
import traceback
from urllib.parse import quote_plus
from typing import Dict, Any, Optional
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


def build_db_uri(database_type: str, host: str, port: int, database: str, username: str, password: str) -> str:
    """Build SQLAlchemy database URI from connection parameters."""
    # Map database types to SQLAlchemy drivers
    driver_map = {
        "postgresql": "postgresql",
        "postgres": "postgresql",
        "mysql": "mysql+pymysql",
        "mariadb": "mysql+pymysql",
        "sqlite": "sqlite",
        "mssql": "mssql+pyodbc",
        "oracle": "oracle+cx_oracle",
    }
    
    driver = driver_map.get(database_type.lower(), database_type.lower())
    
    if database_type.lower() == "sqlite":
        # SQLite uses file path instead of host/port
        return f"sqlite:///{host}"
    else:
        # URL encode username and password to handle special characters
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        return f"{driver}://{encoded_username}:{encoded_password}@{host}:{port}/{database}"


def get_llm(openai_api_key: str):
    """Get LangChain ChatOpenAI instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_api_key,
    )


# SQL generation prompt
SQL_PROMPT = ChatPromptTemplate.from_template(
    """Based on the table schema below, write a SQL query that would answer the user's question.

Schema:
{schema}

Question:
{question}

SQL Query:"""
)


# Final answer prompt
ANSWER_PROMPT = ChatPromptTemplate.from_template(
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


def _extract_sql_from_text(text: str) -> Optional[str]:
    """Extract SQL from model output."""
    # First, try to find a fenced code block with optional "sql" hint
    m = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.S | re.I)
    if m:
        return m.group(1).strip()

    # Otherwise, try to find the first SQL statement starting with a common SQL keyword
    m = re.search(r"(?i)(SELECT|WITH|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b.*", text, re.S)
    if m:
        return text[m.start():].strip()

    return None


def run_query(db: SQLDatabase, query_or_text: str) -> str:
    """Extract SQL from model output and execute it. If no SQL is found,
    return the original text (so the answer chain can use it as a message).
    """
    sql = _extract_sql_from_text(query_or_text)
    if not sql:
        # Nothing executable detected — return the model output unchanged
        return query_or_text

    try:
        # Execute the SQL query
        result = db.run(sql)
        return str(result)
    except Exception as e:
        # Return a clear error message instead of raising, so the answer prompt can include it
        return f"SQL execution error: {e}\n\nOriginal SQL:\n{sql}"


def chat_with_db(
    question: str,
    database_type: str,
    host: str,
    port: int,
    database: str,
    username: str,
    password: str,
    openai_api_key: str,
    custom_tone_schema_enabled: bool = False,
    custom_tone_rows_enabled: bool = False,
    custom_tone_schema: Optional[str] = None,
    custom_tone_rows: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main chat function - processes a question about database data.
    
    Args:
        question: User's question about the database
        database_type: Type of database (postgresql, mysql, etc.)
        host: Database host
        port: Database port
        database: Database name
        username: Database username
        password: Database password
        openai_api_key: OpenAI API key
        custom_tone_schema_enabled: If True, use custom_tone_schema for schema-based answers
        custom_tone_rows_enabled: If True, use custom_tone_rows for row-based answers
        custom_tone_schema: Custom tone/style text for schema-based answers (when enabled)
        custom_tone_rows: Custom tone/style text for row-based answers (when enabled)
    
    Returns:
        {
            "answer": str,
            "resolution_note": str,
            "action": "DESCRIBE" | "QUERY",
            "sql_attempts": list[str],
            "final_sql": str,
            "error": Optional[str]
        }
    """
    try:
        # Build database URI
        db_uri = build_db_uri(database_type, host, port, database, username, password)
        
        # Create SQLDatabase instance with better error handling
        try:
            db = SQLDatabase.from_uri(db_uri)
            # Test the connection by trying to get table info
            try:
                db.get_table_info()
            except Exception as test_error:
                error_msg = str(test_error)
                if "could not translate host name" in error_msg.lower() or "name resolution" in error_msg.lower():
                    raise Exception(f"Could not connect to database host '{host}'. Please check if the host is correct and reachable.")
                elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower() or "access denied" in error_msg.lower():
                    raise Exception(f"Database authentication failed. Please check your username and password.")
                elif "database" in error_msg.lower() and ("does not exist" in error_msg.lower() or "not found" in error_msg.lower()):
                    raise Exception(f"Database '{database}' does not exist. Please check the database name.")
                elif "connection refused" in error_msg.lower() or "connection timeout" in error_msg.lower() or "timeout" in error_msg.lower():
                    raise Exception(f"Connection to database at '{host}:{port}' was refused or timed out. Please check if the database server is running and the port is correct.")
                elif "no module named" in error_msg.lower():
                    # Missing database driver
                    if "psycopg2" in error_msg.lower() or "psycopg" in error_msg.lower():
                        raise Exception(f"PostgreSQL driver not installed. Please install it with: pip install psycopg2-binary")
                    elif "pymysql" in error_msg.lower():
                        raise Exception(f"MySQL driver not installed. Please install it with: pip install pymysql")
                    else:
                        raise Exception(f"Database driver not installed. Error: {error_msg}")
                else:
                    raise Exception(f"Database connection error: {error_msg}")
        except Exception as conn_error:
            error_msg = str(conn_error)
            # If it's already our formatted error, re-raise it
            if "Could not connect" in error_msg or "authentication failed" in error_msg or "does not exist" in error_msg or "Connection to database" in error_msg or "driver not installed" in error_msg:
                raise
            # Otherwise, provide more helpful error messages
            if "could not translate host name" in error_msg.lower() or "name resolution" in error_msg.lower():
                raise Exception(f"Could not connect to database host '{host}'. Please check if the host is correct and reachable.")
            elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower() or "access denied" in error_msg.lower():
                raise Exception(f"Database authentication failed. Please check your username and password.")
            elif "database" in error_msg.lower() and ("does not exist" in error_msg.lower() or "not found" in error_msg.lower()):
                raise Exception(f"Database '{database}' does not exist. Please check the database name.")
            elif "connection refused" in error_msg.lower() or "connection timeout" in error_msg.lower() or "timeout" in error_msg.lower():
                raise Exception(f"Connection to database at '{host}:{port}' was refused or timed out. Please check if the database server is running and the port is correct.")
            elif "no module named" in error_msg.lower():
                # Missing database driver
                if "psycopg2" in error_msg.lower() or "psycopg" in error_msg.lower():
                    raise Exception(f"PostgreSQL driver not installed. Please install it with: pip install psycopg2-binary")
                elif "pymysql" in error_msg.lower():
                    raise Exception(f"MySQL driver not installed. Please install it with: pip install pymysql")
                else:
                    raise Exception(f"Database driver not installed. Error: {error_msg}")
            else:
                raise Exception(f"Database connection error: {error_msg}")
        
        # Initialize LLM
        llm = get_llm(openai_api_key)
        
        # Get schema with error handling
        def get_schema(_):
            try:
                return db.get_table_info()
            except Exception as schema_error:
                error_msg = str(schema_error)
                # Provide more helpful error messages for schema retrieval
                if "could not translate host name" in error_msg.lower() or "name resolution" in error_msg.lower():
                    raise Exception(f"Could not connect to database host '{host}'. Please check if the host is correct and reachable.")
                elif "authentication failed" in error_msg.lower() or "password" in error_msg.lower() or "access denied" in error_msg.lower():
                    raise Exception(f"Database authentication failed. Please check your username and password.")
                elif "database" in error_msg.lower() and ("does not exist" in error_msg.lower() or "not found" in error_msg.lower()):
                    raise Exception(f"Database '{database}' does not exist. Please check the database name.")
                elif "connection refused" in error_msg.lower() or "connection timeout" in error_msg.lower() or "timeout" in error_msg.lower():
                    raise Exception(f"Connection to database at '{host}:{port}' was refused or timed out. Please check if the database server is running and the port is correct.")
                elif "no module named" in error_msg.lower():
                    # Missing database driver
                    if "psycopg2" in error_msg.lower() or "psycopg" in error_msg.lower():
                        raise Exception(f"PostgreSQL driver not installed. Please install it with: pip install psycopg2-binary")
                    elif "pymysql" in error_msg.lower():
                        raise Exception(f"MySQL driver not installed. Please install it with: pip install pymysql")
                    else:
                        raise Exception(f"Database driver not installed. Error: {error_msg}")
                else:
                    raise Exception(f"Failed to retrieve database schema: {error_msg}")
        
        # SQL generation chain
        sql_chain = (
            RunnablePassthrough.assign(schema=get_schema)
            | SQL_PROMPT
            | llm.bind(stop=["\nSQLResult:"])
            | StrOutputParser()
        )
        
        # Determine tone for answer prompt
        answer_tone = (
            custom_tone_rows.strip()
            if custom_tone_rows_enabled and custom_tone_rows
            else """You are a helpful, friendly data assistant.

Style:
- Conversational
- Brief and precise
- Prefer short bullets when listing

Grounding:
- Do NOT invent values.
- Only use what appears in the SQL response."""
        )
        
        # Create answer prompt with custom tone
        answer_prompt_with_tone = ChatPromptTemplate.from_template(
            f"""{answer_tone}

Schema:
{{schema}}

Question:
{{question}}

SQL Query:
{{query}}

SQL Response:
{{response}}

Answer:"""
        )
        
        # Full chain: generate SQL, execute it, then generate answer
        full_chain = (
            RunnablePassthrough.assign(query=sql_chain).assign(
                schema=get_schema,
                response=lambda vars: run_query(db, vars["query"]),
            )
            | answer_prompt_with_tone
            | llm
        )
        
        # Invoke the chain
        result = full_chain.invoke({"question": question})
        
        # Extract SQL attempts (we'll track the final query)
        # Note: For simplicity, we're not tracking multiple attempts like PowerBI does
        # But we can extract the SQL from the chain if needed
        sql_attempts = []
        final_sql = ""
        
        # Try to extract SQL from the chain execution
        # We need to run the SQL chain separately to get the SQL
        try:
            sql_result = sql_chain.invoke({"question": question})
            sql_query = _extract_sql_from_text(sql_result) or sql_result.strip()
            if sql_query:
                sql_attempts.append(sql_query)
                final_sql = sql_query
        except Exception:
            pass
        
        return {
            "answer": result.content.strip(),
            "resolution_note": "",
            "action": "QUERY" if final_sql else "DESCRIBE",
            "sql_attempts": sql_attempts,
            "final_sql": final_sql,
            "error": None,
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        # Get full traceback for debugging
        tb_str = traceback.format_exc()
        
        # Handle OpenAI API errors specifically
        if "APIConnectionError" in error_type or "api connection" in error_msg.lower():
            detailed_error = (
                "OpenAI API connection failed. This could be due to:\n"
                "- Network connectivity issues\n"
                "- OpenAI API service is temporarily unavailable\n"
                "- Firewall or proxy blocking the connection\n"
                "- Invalid or expired API key\n\n"
                f"Error details: {error_msg}"
            )
        elif "APIError" in error_type or "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            detailed_error = (
                "OpenAI API authentication failed. Please check:\n"
                "- Your OpenAI API key is valid and not expired\n"
                "- The API key has sufficient credits\n"
                "- The API key has the correct permissions\n\n"
                f"Error details: {error_msg}"
            )
        elif "RateLimitError" in error_type or "rate limit" in error_msg.lower():
            detailed_error = (
                "OpenAI API rate limit exceeded. Please:\n"
                "- Wait a few moments and try again\n"
                "- Check your OpenAI API usage limits\n"
                "- Consider upgrading your OpenAI plan\n\n"
                f"Error details: {error_msg}"
            )
        # Provide more detailed error information
        # If the error message is too generic, include more details
        elif error_msg == "Connection error" or error_msg.lower() == "connection error":
            # Try to extract more information from traceback
            if "psycopg2" in tb_str.lower() or "psycopg" in tb_str.lower():
                if "could not translate host name" in tb_str.lower():
                    detailed_error = f"Could not connect to database host '{host}'. Please check if the host is correct and reachable."
                elif "authentication failed" in tb_str.lower() or "password" in tb_str.lower():
                    detailed_error = f"Database authentication failed. Please check your username and password."
                elif "connection refused" in tb_str.lower():
                    detailed_error = f"Connection to database at '{host}:{port}' was refused. Please check if the database server is running and the port is correct."
                elif "timeout" in tb_str.lower():
                    detailed_error = f"Connection to database at '{host}:{port}' timed out. Please check if the database server is running and accessible."
                elif "no module named" in tb_str.lower():
                    detailed_error = f"PostgreSQL driver not installed. Please install it with: pip install psycopg2-binary"
                else:
                    detailed_error = f"Database connection error. Full error: {tb_str[-500:]}"  # Last 500 chars of traceback
            elif "pymysql" in tb_str.lower():
                if "access denied" in tb_str.lower() or "authentication" in tb_str.lower():
                    detailed_error = f"Database authentication failed. Please check your username and password."
                elif "connection refused" in tb_str.lower():
                    detailed_error = f"Connection to database at '{host}:{port}' was refused. Please check if the database server is running and the port is correct."
                elif "no module named" in tb_str.lower():
                    detailed_error = f"MySQL driver not installed. Please install it with: pip install pymysql"
                else:
                    detailed_error = f"Database connection error. Full error: {tb_str[-500:]}"
            else:
                # Generic connection error - try to provide more info
                detailed_error = f"Database connection failed. Error type: {error_type}. Details: {tb_str[-500:]}"
        else:
            detailed_error = f"{error_type}: {error_msg}"
        
        return {
            "answer": f"An error occurred while processing your question: {detailed_error}",
            "resolution_note": "",
            "action": "ERROR",
            "sql_attempts": [],
            "final_sql": "",
            "error": detailed_error,
        }

