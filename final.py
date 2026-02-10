# power_bi/final.py
# Power BI "chat-on-data" CLI (LLM-first) with:
# - Your exact auth logic (app-only if PBI_CLIENT_SECRET exists, else delegated device-code)
# - Schema cached once via INFO.VIEW.* (context only, NOT routing)
# - NO hardcoded command routing (LLM decides everything)
# - Planner decides: DESCRIBE (answer from schema) vs QUERY (run DAX)
# - Feedback loop for QUERY: on execution error, send error back to LLM and retry (max 2)
# - Fixed schema parsing: supports bracketed keys like "[Name]" "[Table]" etc.
# - Typo/value resolution: samples candidate values from likely columns and lets LLM resolve "Jo janx" -> "JO-JanX"
# - More human + brief answers
#
# Run:
#   python power_bi/final.py

import os
import re
import json
import requests
import msal
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI


# -----------------------------
# Load env
# -----------------------------
load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

TENANT_ID = os.environ["PBI_TENANT_ID"]
CLIENT_ID = os.environ["PBI_CLIENT_ID"]
GROUP_ID = os.environ["PBI_GROUP_ID"]
DATASET_ID = os.environ["PBI_DATASET_ID"]

SCOPES = ["https://analysis.windows.net/powerbi/api/Dataset.Read.All"]
APP_SCOPES = ["https://analysis.windows.net/powerbi/api/.default"]

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
CACHE_FILE = ".msal_token_cache.json"


# -----------------------------
# Auth (EXACT same logic as yours)
# -----------------------------
def load_cache() -> msal.SerializableTokenCache:
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache.deserialize(f.read())
    return cache


def save_cache(cache: msal.SerializableTokenCache) -> None:
    if cache.has_state_changed:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(cache.serialize())


def get_token_same_as_yours() -> str:
    cache = load_cache()

    client_secret = os.environ.get("PBI_CLIENT_SECRET")
    if client_secret:
        app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=client_secret,
            authority=AUTHORITY,
            token_cache=cache,
        )

        result = app.acquire_token_silent(APP_SCOPES, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=APP_SCOPES)

        if not result or "access_token" not in result:
            raise RuntimeError("Failed to obtain app token:\n" + json.dumps(result or {}, indent=2))

        save_cache(cache)
        return result["access_token"]

    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            save_cache(cache)
            return result["access_token"]

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "message" not in flow:
        raise RuntimeError(f"Could not initiate device flow. Details: {flow}")

    print("\n=== Microsoft Login Required ===")
    print(flow["message"])
    print("================================\n")

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError("Failed to obtain token:\n" + json.dumps(result, indent=2))

    save_cache(cache)
    return result["access_token"]


# -----------------------------
# Power BI executeQueries
# -----------------------------
def execute_dax(token: str, dax: str) -> dict:
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{GROUP_ID}/datasets/{DATASET_ID}/executeQueries"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"queries": [{"query": dax}], "serializerSettings": {"includeNulls": True}}
    r = requests.post(url, headers=headers, json=payload, timeout=60)

    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}

    if r.status_code >= 400:
        raise RuntimeError(f"executeQueries failed ({r.status_code}):\n{json.dumps(data, indent=2)}")

    return data


def _first_table_rows(resp_json: dict) -> list[dict]:
    return (
        resp_json.get("results", [{}])[0]
        .get("tables", [{}])[0]
        .get("rows", [])
    )


# -----------------------------
# Schema parsing helpers (handles bracketed keys like "[Name]")
# -----------------------------
def _get_any(row: dict, keys: list[str]):
    for k in keys:
        if k in row and row[k] not in (None, "", []):
            return row[k]
        bk = f"[{k}]"
        if bk in row and row[bk] not in (None, "", []):
            return row[bk]
    return None


def _norm(v):
    return str(v).strip() if v is not None else None


# -----------------------------
# Schema builder (context only)
# -----------------------------
def build_schema_string(token: str) -> str:
    dax_tables = "EVALUATE INFO.VIEW.TABLES()"
    dax_cols = "EVALUATE INFO.VIEW.COLUMNS()"
    dax_rels = "EVALUATE INFO.VIEW.RELATIONSHIPS()"
    dax_meas = "EVALUATE INFO.VIEW.MEASURES()"

    tables = _first_table_rows(execute_dax(token, dax_tables))
    cols = _first_table_rows(execute_dax(token, dax_cols))
    rels = _first_table_rows(execute_dax(token, dax_rels))
    meas = _first_table_rows(execute_dax(token, dax_meas))

    table_names: list[str] = []
    for t in tables:
        name = _norm(_get_any(t, ["Name", "Table", "TableName"]))
        if name:
            table_names.append(name)

    col_lines: list[str] = []
    for c in cols:
        table = _norm(_get_any(c, ["Table", "TableName"]))
        col = _norm(_get_any(c, ["Name", "Column", "ColumnName"]))
        dtype = _norm(_get_any(c, ["DataType", "Type"]))
        if table and col:
            col_lines.append(f"- {table}[{col}] : {dtype or ''}".rstrip())

    meas_lines: list[str] = []
    for m in meas:
        table = _norm(_get_any(m, ["Table", "TableName"]))
        name = _norm(_get_any(m, ["Name", "Measure", "MeasureName"]))
        expr = _get_any(m, ["Expression", "DaxExpression"])
        expr_str = str(expr) if expr is not None else ""
        if table and name:
            expr_short = (expr_str[:220] + "…") if len(expr_str) > 220 else expr_str
            meas_lines.append(f"- {table}[{name}] = {expr_short}")

    rel_lines: list[str] = []
    for r in rels:
        ft = _norm(_get_any(r, ["FromTable"]))
        fc = _norm(_get_any(r, ["FromColumn"]))
        tt = _norm(_get_any(r, ["ToTable"]))
        tc = _norm(_get_any(r, ["ToColumn"]))
        if ft and fc and tt and tc:
            rel_lines.append(f"- {ft}[{fc}] -> {tt}[{tc}]")

    if len(table_names) == 0 and len(col_lines) == 0 and len(meas_lines) == 0 and len(rel_lines) == 0:
        raise RuntimeError(
            "Schema extraction produced an empty schema. INFO.VIEW returned rows but keys weren't parsed as expected."
        )

    lines: list[str] = []
    lines.append("TABLES:")
    for n in sorted(set(table_names)):
        lines.append(f"- {n}")

    lines.append("\nCOLUMNS (Table[Column] : DataType):")
    lines.extend(col_lines[:30000])

    lines.append("\nMEASURES (Table[Measure] = Expression):")
    lines.extend(meas_lines[:12000])

    lines.append("\nRELATIONSHIPS (From -> To):")
    lines.extend(rel_lines[:12000])

    return "\n".join(lines).strip()


# -----------------------------
# LLM
# -----------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY,
)


# -----------------------------
# Prompts
# -----------------------------
plan_prompt = ChatPromptTemplate.from_template(
    """Decide how to answer a question about a Power BI semantic model.

You have a schema snapshot (tables, columns, measures, relationships). You can either:
- DESCRIBE: answer using only the schema (no DAX execution)
- QUERY: generate a DAX query to execute (executeQueries), then answer from results

Return ONLY valid JSON with keys:
- "action": "DESCRIBE" or "QUERY"
- "reason": short reason
- "dax": a DAX query string if action is "QUERY", otherwise ""

Rules for QUERY:
- Use ONLY names present in the schema.
- Always use EVALUATE with a table expression.
- Quote table names with spaces/hyphens using single quotes, e.g. 'Dim Date'.
- Prefer querying real data tables rather than inventing lists of names.

Schema:
{schema}

Question:
{question}

JSON:"""
)

dax_prompt = ChatPromptTemplate.from_template(
    """Generate DAX for Power BI executeQueries.

Hard rules (must follow):
1) Only use tables/columns/measures that appear in the schema.
2) Return ONLY the DAX query inside a ```dax code block. No explanation.
3) Always return a table result using EVALUATE.
4) Column references MUST use the exact DAX form: 'Table'[Column]
   - Never write 'Table[Column]' (that is invalid).
5) Table references:
  - Always use 'Table'[Column] form.
  - If a table name contains spaces/symbols OR starts with underscore, ALWAYS wrap it in single quotes: '_Daly Production'[createdAt].
6) If the user asks for a total / count / average / min / max:
   - Return exactly ONE row using:
     EVALUATE ROW("Result", <number>)
   - Use CALCULATE/SUM/COUNTROWS/SUMX/AVERAGEX as needed.
7) If the user asks to list items:
   - Return a table with human-friendly columns (names over IDs when possible).
   - Limit output: TOPN(50, ..., <sort>, ASC/DESC)
8) When filtering by date ranges:
   - Prefer half-open intervals: >= start AND < next period start (safer than <= end).
9) For text matching or “I don’t remember exact name”:
   - Use CONTAINSSTRING( LOWER( 'Table'[TextCol] ), LOWER("value") ) where appropriate.



Schema:
{schema}

Question:
{question}

DAX Query:"""
)



fix_prompt = ChatPromptTemplate.from_template(
    """The previous DAX query failed in Power BI executeQueries.

Schema:
{schema}

Question:
{question}

Failed DAX:
{dax}

Power BI error:
{error}

Write a corrected DAX query.

Hard rules (must follow):
1) Only use tables/columns/measures that appear in the schema.
2) Return ONLY the DAX query inside a ```dax code block.
3) Always return a table result using EVALUATE.
4) Column references MUST use: 'Table'[Column] (never 'Table[Column]').
5) If the user asks for a total / count / average / min / max:
   - Return exactly ONE row:
     EVALUATE ROW("Result", <number>)
6) Prefer human-friendly columns (names) over IDs when possible.
7) Keep results small: TOPN(50, ...) for list outputs.
8) Table references:
  - Always use 'Table'[Column] form.
  - If a table name contains spaces/symbols OR starts with underscore, ALWAYS wrap it in single quotes: '_Daly Production'[createdAt].

DAX Query:"""
)



answer_from_schema_prompt = ChatPromptTemplate.from_template(
    """You are a helpful, friendly data assistant.

Style:
- Conversational
- Brief and precise
- Human-friendly naming

Important presentation rules:
- When listing tables for a user:
  - EXCLUDE system or auto-generated date tables unless the user explicitly asks for them.
  - Examples of system tables include tables used only for internal date handling
    (often with long generated names).
  - Prefer business-facing tables (facts, dimensions, entities).
- If the user explicitly asks for "all tables" or "including system tables",
  then include everything.

Grounding:
- Use ONLY what exists in the schema snapshot.
- Do NOT invent tables.

Schema:
{schema}

Question:
{question}

Answer:"""
)


answer_from_rows_prompt = ChatPromptTemplate.from_template(
    """You are a helpful, friendly data assistant.

Style:
- Conversational
- Brief and precise
- Prefer short bullets when listing

Grounding:
- Do NOT invent values.
- Only use what appears in the response rows.

Question:
{question}

Final Executed DAX:
{final_dax}

Response rows:
{response}

Answer:"""
)

value_resolution_plan_prompt = ChatPromptTemplate.from_template(
    """You help detect likely user-typed values (may contain typos) and decide what values to sample.

Schema:
{schema}

User question:
{question}

Return ONLY JSON:
{{
  "need_resolution": true/false,
  "targets": [
    {{"table": "...", "column": "...", "why": "short reason"}}
  ],
  "user_value": "string the user likely refers to (exact substring or normalized)",
  "rewrite_question": "question rewritten to be clearer, keeping intent. If no change, same question."
}}

Rules:
- Only propose targets that exist in the schema.
- Only choose a small number of targets (<= 3), likely text columns (names/labels).
- If the question does not reference a specific entity/value, set need_resolution=false.
"""
)

value_resolution_prompt = ChatPromptTemplate.from_template(
    """Resolve user value typos using candidate values sampled from the data.

User value (may be typo):
{user_value}

Candidate values:
{values}

Return ONLY JSON:
{{
  "resolved": string or null,
  "alternatives": [string]
}}

Rules:
- If a clear best match exists, set resolved to that exact candidate string.
- If multiple are close, put top 3 in alternatives and set resolved=null.
- If none are close, resolved=null and alternatives=[]
"""
)


# -----------------------------
# Utilities
# -----------------------------
def parse_json_maybe(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}
    return {}


def _extract_dax(text: str) -> str | None:
    m = re.search(r"```(?:dax)?\s*(.*?)\s*```", text, re.S | re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?i)\bEVALUATE\b.*", text, re.S)
    if m:
        return text[m.start():].strip()
    return None


def generate_dax(schema: str, question: str) -> str:
    return (dax_prompt | llm | StrOutputParser()).invoke({"schema": schema, "question": question})


def generate_fixed_dax(schema: str, question: str, failed_dax: str, error: str) -> str:
    return (fix_prompt | llm | StrOutputParser()).invoke(
        {"schema": schema, "question": question, "dax": failed_dax, "error": error}
    )


# -----------------------------
# Typo / value resolution
# -----------------------------
def parse_schema_text_columns(schema_text: str) -> list[tuple[str, str]]:
    """
    Extract (table, column) pairs for Text columns from the schema snapshot.
    """
    pairs: list[tuple[str, str]] = []
    for line in schema_text.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        # "- Table[Column] : DataType"
        m = re.match(r"-\s+(.+?)\[(.+?)\]\s*:\s*(.+)$", line)
        if not m:
            continue
        table, col, dtype = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if dtype.lower() == "text":
            pairs.append((table, col))
    return pairs


def sample_distinct_values(token: str, table: str, column: str, limit: int = 50) -> list[str]:
    dax = f"""
EVALUATE
TOPN(
    {limit},
    DISTINCT(SELECTCOLUMNS('{table}', "value", '{table}'[{column}])),
    [value], ASC
)
""".strip()
    try:
        rows = _first_table_rows(execute_dax(token, dax))
        vals = []
        for r in rows:
            v = r.get("value")
            if v is not None and str(v).strip() != "":
                vals.append(str(v))
        return vals
    except Exception:
        return []


def resolve_user_value_if_needed(token: str, schema: str, question: str) -> tuple[str, str]:
    """
    Returns: (maybe_rewritten_question, resolution_note)
    resolution_note is "" or a short note like "Interpreting 'Jo janx' as 'JO-JanX'."
    """
    if not schema.strip():
        return question, ""

    text_cols = parse_schema_text_columns(schema)
    if not text_cols:
        return question, ""

    plan_text = (value_resolution_plan_prompt | llm | StrOutputParser()).invoke({"schema": schema, "question": question})
    plan = parse_json_maybe(plan_text)

    need = bool(plan.get("need_resolution", False))
    if not need:
        # still allow rewrite_question (clarify wording) without value resolution
        rq = (plan.get("rewrite_question") or "").strip() or question
        return rq, ""

    targets = plan.get("targets") or []
    user_value = (plan.get("user_value") or "").strip()
    rewrite_question = (plan.get("rewrite_question") or "").strip() or question

    if not user_value or not isinstance(targets, list) or len(targets) == 0:
        return rewrite_question, ""

    # Sample candidates from up to 3 targets
    collected: list[str] = []
    for t in targets[:3]:
        table = (t.get("table") or "").strip()
        col = (t.get("column") or "").strip()
        if not table or not col:
            continue
        collected.extend(sample_distinct_values(token, table, col, limit=60))

    # Deduplicate and cap
    uniq = []
    seen = set()
    for v in collected:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
        if len(uniq) >= 120:
            break

    if not uniq:
        return rewrite_question, ""

    res_text = (value_resolution_prompt | llm | StrOutputParser()).invoke(
        {"user_value": user_value, "values": json.dumps(uniq, ensure_ascii=False)}
    )
    res = parse_json_maybe(res_text)

    resolved = res.get("resolved")
    alts = res.get("alternatives") or []

    if isinstance(resolved, str) and resolved.strip():
        # Replace occurrences loosely (case-insensitive) if present, otherwise append clarification
        resolved = resolved.strip()
        # try replace user_value substring if it exists
        if user_value and user_value.lower() in rewrite_question.lower():
            pattern = re.compile(re.escape(user_value), re.I)
            new_q = pattern.sub(resolved, rewrite_question)
        else:
            new_q = f"{rewrite_question} (value: {resolved})"
        note = f"Interpreting '{user_value}' as '{resolved}'."
        return new_q, note

    # If multiple close alternatives, ask in chat later via note
    if isinstance(alts, list) and len(alts) > 0:
        note = f"I found similar values for '{user_value}': {', '.join(alts[:3])}. If you meant one of these, tell me."
        return rewrite_question, note

    return rewrite_question, ""


# -----------------------------
# Feedback-loop execution
# -----------------------------
def execute_with_feedback(token: str, schema: str, question: str, initial_dax_text: str, max_retries: int = 2):
    attempt_logs: list[str] = []
    dax_text = initial_dax_text

    for attempt in range(max_retries + 1):
        dax = _extract_dax(dax_text) or dax_text.strip()
        if not dax or "EVALUATE" not in dax.upper():
            return "", dax_text, attempt_logs

        attempt_logs.append(dax)

        print(f"\n--- Executing DAX (attempt {attempt + 1}/{max_retries + 1}) ---")
        print(dax)
        print("--- End DAX ---\n")

        try:
            resp = execute_dax(token, dax)
            rows = _first_table_rows(resp)
            return dax, json.dumps(rows[:200], indent=2), attempt_logs
        except Exception as e:
            err = str(e)
            if attempt == max_retries:
                return dax, f"DAX execution error: {err}\n\nLast attempted DAX:\n{dax}", attempt_logs
            dax_text = generate_fixed_dax(schema=schema, question=question, failed_dax=dax, error=err)

    return "", "Unexpected state in feedback loop", attempt_logs


# -----------------------------
# Main loop
# -----------------------------
def main():
    print("Connecting to Power BI...")
    token = get_token_same_as_yours()
    print("✅ Connected to Power BI.")
    print("Workspace:", GROUP_ID)
    print("Dataset:  ", DATASET_ID)

    schema_cache = ""
    try:
        print("\nLoading schema via INFO.VIEW.* (this may take a moment)...")
        schema_cache = build_schema_string(token)
        print("✅ Schema loaded.\n")

        preview = "\n".join(schema_cache.splitlines()[:25])
        print("Schema preview (first 25 lines):")
        print(preview)
        print("... (truncated)\n")

    except Exception as e:
        print("\n⚠️ Could not load schema via INFO.VIEW.*")
        print("   Error:")
        print(e)
        schema_cache = ""

    print("Ask a question (type 'exit' to quit)\n")

    while True:
        question_raw = input("You: ").strip()
        if question_raw.lower() in {"exit", "quit"}:
            break

        # 0) Try resolve user-typed value typos (optional, LLM-driven; no hardcoded routing)
        question, resolution_note = resolve_user_value_if_needed(token, schema_cache, question_raw)

        # 1) Planner decides DESCRIBE vs QUERY
        plan_text = (plan_prompt | llm | StrOutputParser()).invoke({"schema": schema_cache, "question": question})
        plan = parse_json_maybe(plan_text)

        action = (plan.get("action") or "").strip().upper()
        dax_from_plan = (plan.get("dax") or "").strip()

        # 2) DESCRIBE (no DAX execution)
        if action == "DESCRIBE" or not action:
            answer = (answer_from_schema_prompt | llm).invoke({"schema": schema_cache, "question": question})
            print("\nAI:")
            if resolution_note:
                print(resolution_note)
            print(answer.content.strip())
            print("\n" + "-" * 60 + "\n")
            continue

        # 3) QUERY (execute + feedback loop)
        if action == "QUERY":
            initial_dax_text = dax_from_plan if dax_from_plan else generate_dax(schema_cache, question)

            final_dax, response_text, _attempts = execute_with_feedback(
                token=token,
                schema=schema_cache,
                question=question,
                initial_dax_text=initial_dax_text,
                max_retries=2,
            )

            answer = (answer_from_rows_prompt | llm).invoke(
                {"question": question, "final_dax": final_dax or "(no DAX executed)", "response": response_text}
            )

            print("\nAI:")
            if resolution_note:
                print(resolution_note)
            print(answer.content.strip())
            print("\n" + "-" * 60 + "\n")
            continue

        # Fallback: unexpected planner output -> describe
        answer = (answer_from_schema_prompt | llm).invoke({"schema": schema_cache, "question": question})
        print("\nAI:")
        if resolution_note:
            print(resolution_note)
        print(answer.content.strip())
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
