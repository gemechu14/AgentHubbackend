"""
Power BI Chat Service - Implements chat-on-data functionality from final.py
"""
import os
import json
import re
from typing import Dict, Any, Optional, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from app.services.powerbi_service import (
    get_powerbi_token,
    execute_dax,
    get_schema_dax,
)

# Simple in-memory schema cache (keyed by workspace_id + dataset_id)
_schema_cache: Dict[str, str] = {}


# Initialize LLM
def get_llm(openai_api_key: str):
    """Get LangChain ChatOpenAI instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=openai_api_key,
    )


# Prompts (from final.py)
PLAN_PROMPT = ChatPromptTemplate.from_template(
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

DAX_PROMPT = ChatPromptTemplate.from_template(
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
9) For text matching or "I don't remember exact name":
   - Use CONTAINSSTRING( LOWER( 'Table'[TextCol] ), LOWER("value") ) where appropriate.


Schema:
{schema}

Question:
{question}

DAX Query:"""
)

FIX_PROMPT = ChatPromptTemplate.from_template(
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

ANSWER_FROM_SCHEMA_PROMPT = ChatPromptTemplate.from_template(
    """
{tone}


Schema:
{schema}

Question:
{question}

Answer:"""
)

ANSWER_FROM_ROWS_PROMPT = ChatPromptTemplate.from_template(
    """
{tone}

Question:
{question}

Final Executed DAX:
{final_dax}

Response rows:
{response}

Answer:"""
)

VALUE_RESOLUTION_PLAN_PROMPT = ChatPromptTemplate.from_template(
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

VALUE_RESOLUTION_PROMPT = ChatPromptTemplate.from_template(
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


# Utility functions
def parse_json_maybe(text: str) -> dict:
    """Parse JSON from text, trying multiple methods."""
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


def _extract_dax(text: str) -> Optional[str]:
    """Extract DAX query from text."""
    m = re.search(r"```(?:dax)?\s*(.*?)\s*```", text, re.S | re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r"(?i)\bEVALUATE\b.*", text, re.S)
    if m:
        return text[m.start():].strip()
    return None


def _first_table_rows(resp_json: dict) -> list[dict]:
    """Extract rows from first table in Power BI response."""
    return (
        resp_json.get("results", [{}])[0]
        .get("tables", [{}])[0]
        .get("rows", [])
    )


def _get_any(row: dict, keys: list[str]):
    """Get value from row using multiple possible keys (handles bracketed keys)."""
    for k in keys:
        if k in row and row[k] not in (None, "", []):
            return row[k]
        bk = f"[{k}]"
        if bk in row and row[bk] not in (None, "", []):
            return row[bk]
    return None


def _norm(v):
    """Normalize value."""
    return str(v).strip() if v is not None else None


def build_schema_string(token: str, workspace_id: str, dataset_id: str) -> str:
    """Build schema string from Power BI INFO.VIEW queries."""
    dax_tables = "EVALUATE INFO.VIEW.TABLES()"
    dax_cols = "EVALUATE INFO.VIEW.COLUMNS()"
    dax_rels = "EVALUATE INFO.VIEW.RELATIONSHIPS()"
    dax_meas = "EVALUATE INFO.VIEW.MEASURES()"

    tables = _first_table_rows(execute_dax(token, workspace_id, dataset_id, dax_tables))
    cols = _first_table_rows(execute_dax(token, workspace_id, dataset_id, dax_cols))
    rels = _first_table_rows(execute_dax(token, workspace_id, dataset_id, dax_rels))
    meas = _first_table_rows(execute_dax(token, workspace_id, dataset_id, dax_meas))

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


def parse_schema_text_columns(schema_text: str) -> list[tuple[str, str]]:
    """Extract (table, column) pairs for Text columns from schema."""
    pairs: list[tuple[str, str]] = []
    for line in schema_text.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        m = re.match(r"-\s+(.+?)\[(.+?)\]\s*:\s*(.+)$", line)
        if not m:
            continue
        table, col, dtype = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
        if dtype.lower() == "text":
            pairs.append((table, col))
    return pairs


def sample_distinct_values(token: str, workspace_id: str, dataset_id: str, table: str, column: str, limit: int = 50) -> list[str]:
    """Sample distinct values from a column."""
    dax = f"""
EVALUATE
TOPN(
    {limit},
    DISTINCT(SELECTCOLUMNS('{table}', "value", '{table}'[{column}])),
    [value], ASC
)
""".strip()
    try:
        rows = _first_table_rows(execute_dax(token, workspace_id, dataset_id, dax))
        vals = []
        for r in rows:
            v = r.get("value")
            if v is not None and str(v).strip() != "":
                vals.append(str(v))
        return vals
    except Exception:
        return []


def resolve_user_value_if_needed(
    llm: ChatOpenAI,
    token: str,
    workspace_id: str,
    dataset_id: str,
    schema: str,
    question: str
) -> Tuple[str, str]:
    """
    Resolve user value typos if needed.
    Returns: (maybe_rewritten_question, resolution_note)
    """
    if not schema.strip():
        return question, ""

    text_cols = parse_schema_text_columns(schema)
    if not text_cols:
        return question, ""

    plan_text = (VALUE_RESOLUTION_PLAN_PROMPT | llm | StrOutputParser()).invoke({"schema": schema, "question": question})
    plan = parse_json_maybe(plan_text)

    need = bool(plan.get("need_resolution", False))
    if not need:
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
        collected.extend(sample_distinct_values(token, workspace_id, dataset_id, table, col, limit=60))

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

    res_text = (VALUE_RESOLUTION_PROMPT | llm | StrOutputParser()).invoke(
        {"user_value": user_value, "values": json.dumps(uniq, ensure_ascii=False)}
    )
    res = parse_json_maybe(res_text)

    resolved = res.get("resolved")
    alts = res.get("alternatives") or []

    if isinstance(resolved, str) and resolved.strip():
        resolved = resolved.strip()
        if user_value and user_value.lower() in rewrite_question.lower():
            pattern = re.compile(re.escape(user_value), re.I)
            new_q = pattern.sub(resolved, rewrite_question)
        else:
            new_q = f"{rewrite_question} (value: {resolved})"
        note = f"Interpreting '{user_value}' as '{resolved}'."
        return new_q, note

    if isinstance(alts, list) and len(alts) > 0:
        note = f"I found similar values for '{user_value}': {', '.join(alts[:3])}. If you meant one of these, tell me."
        return rewrite_question, note

    return rewrite_question, ""


def execute_with_feedback(
    llm: ChatOpenAI,
    token: str,
    workspace_id: str,
    dataset_id: str,
    schema: str,
    question: str,
    initial_dax_text: str,
    max_retries: int = 2
) -> Tuple[str, str, list[str]]:
    """Execute DAX with feedback loop for error correction."""
    attempt_logs: list[str] = []
    dax_text = initial_dax_text

    for attempt in range(max_retries + 1):
        dax = _extract_dax(dax_text) or dax_text.strip()
        if not dax or "EVALUATE" not in dax.upper():
            return "", dax_text, attempt_logs

        attempt_logs.append(dax)

        try:
            resp = execute_dax(token, workspace_id, dataset_id, dax)
            rows = _first_table_rows(resp)
            return dax, json.dumps(rows[:200], indent=2), attempt_logs
        except Exception as e:
            err = str(e)
            if attempt == max_retries:
                return dax, f"DAX execution error: {err}\n\nLast attempted DAX:\n{dax}", attempt_logs
            dax_text = (FIX_PROMPT | llm | StrOutputParser()).invoke(
                {"schema": schema, "question": question, "dax": dax, "error": err}
            )

    return "", "Unexpected state in feedback loop", attempt_logs


def chat_with_powerbi(
    question: str,
    tenant_id: str,
    client_id: str,
    workspace_id: str,
    dataset_id: str,
    client_secret: str,
    openai_api_key: str,
    custom_tone_schema_enabled: bool = False,
    custom_tone_rows_enabled: bool = False,
    custom_tone_schema: Optional[str] = None,
    custom_tone_rows: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Main chat function - processes a question about Power BI data.
    
    Schema is automatically cached in memory per workspace+dataset combination.
    
    Args:
        question: User's question about the Power BI data
        tenant_id: Azure AD tenant ID
        client_id: Azure AD client ID
        workspace_id: Power BI workspace ID
        dataset_id: Power BI dataset ID
        client_secret: Azure AD client secret
        openai_api_key: OpenAI API key
        custom_tone_schema_enabled: If True, use custom_tone_schema for ANSWER_FROM_SCHEMA_PROMPT
        custom_tone_rows_enabled: If True, use custom_tone_rows for ANSWER_FROM_ROWS_PROMPT
        custom_tone_schema: Custom tone/style text for schema-based answers (when enabled)
        custom_tone_rows: Custom tone/style text for row-based answers (when enabled)
    
    Returns:
        {
            "answer": str,
            "resolution_note": str,
            "action": "DESCRIBE" | "QUERY",
            "dax_attempts": list[str],
            "final_dax": str,
            "error": Optional[str]
        }
    """
    # Get Power BI token
    token = get_powerbi_token(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret,
    )

    # Get or build schema (cached in memory)
    cache_key = f"{workspace_id}:{dataset_id}"
    schema_cache = _schema_cache.get(cache_key)
    
    if not schema_cache:
        try:
            schema_cache = build_schema_string(token, workspace_id, dataset_id)
            # Cache the schema
            _schema_cache[cache_key] = schema_cache
        except Exception as e:
            return {
                "answer": f"Failed to load schema: {str(e)}",
                "resolution_note": "",
                "action": "ERROR",
                "dax_attempts": [],
                "final_dax": "",
                "error": str(e),
            }
    else:
        # Validate cached schema is not empty
        if not schema_cache.strip():
            try:
                schema_cache = build_schema_string(token, workspace_id, dataset_id)
                _schema_cache[cache_key] = schema_cache
            except Exception as e:
                return {
                    "answer": f"Failed to reload schema: {str(e)}",
                    "resolution_note": "",
                    "action": "ERROR",
                    "dax_attempts": [],
                    "final_dax": "",
                    "error": str(e),
                }

    # Initialize LLM
    llm = get_llm(openai_api_key)

    # Resolve user value typos if needed
    question, resolution_note = resolve_user_value_if_needed(
        llm, token, workspace_id, dataset_id, schema_cache, question
    )

    # Planner decides DESCRIBE vs QUERY
    plan_text = (PLAN_PROMPT | llm | StrOutputParser()).invoke({"schema": schema_cache, "question": question})
    plan = parse_json_maybe(plan_text)

    action = (plan.get("action") or "").strip().upper()
    dax_from_plan = (plan.get("dax") or "").strip()

    # DESCRIBE (no DAX execution)
    if action == "DESCRIBE" or not action:
        # Determine tone for schema prompt
        schema_tone = (
            custom_tone_schema.strip()
            if custom_tone_schema_enabled and custom_tone_schema
            else """You are a helpful, friendly data assistant.

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
- Do NOT invent tables."""
        )
        answer = (ANSWER_FROM_SCHEMA_PROMPT | llm).invoke({
            "schema": schema_cache,
            "question": question,
            "tone": schema_tone
        })
        return {
            "answer": answer.content.strip(),
            "resolution_note": resolution_note,
            "action": "DESCRIBE",
            "dax_attempts": [],
            "final_dax": "",
            "error": None,
        }

    # QUERY (execute + feedback loop)
    if action == "QUERY":
        initial_dax_text = dax_from_plan if dax_from_plan else (DAX_PROMPT | llm | StrOutputParser()).invoke(
            {"schema": schema_cache, "question": question}
        )

        final_dax, response_text, attempts = execute_with_feedback(
            llm=llm,
            token=token,
            workspace_id=workspace_id,
            dataset_id=dataset_id,
            schema=schema_cache,
            question=question,
            initial_dax_text=initial_dax_text,
            max_retries=2,
        )

        # Determine tone for rows prompt
        rows_tone = (
            custom_tone_rows.strip()
            if custom_tone_rows_enabled and custom_tone_rows
            else """You are a helpful, friendly data assistant.

Style:
- Conversational
- Brief and precise
- Prefer short bullets when listing

Grounding:
- Do NOT invent values.
- Only use what appears in the response rows."""
        )
        answer = (ANSWER_FROM_ROWS_PROMPT | llm).invoke({
            "question": question,
            "final_dax": final_dax or "(no DAX executed)",
            "response": response_text,
            "tone": rows_tone
        })

        return {
            "answer": answer.content.strip(),
            "resolution_note": resolution_note,
            "action": "QUERY",
            "dax_attempts": attempts,
            "final_dax": final_dax,
            "error": None if final_dax else "DAX execution failed",
        }

    # Fallback: unexpected planner output -> describe
    # Determine tone for schema prompt
    schema_tone = (
        custom_tone_schema.strip()
        if custom_tone_schema_enabled and custom_tone_schema
        else """You are a helpful, friendly data assistant.

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
- Do NOT invent tables."""
    )
    answer = (ANSWER_FROM_SCHEMA_PROMPT | llm).invoke({
        "schema": schema_cache,
        "question": question,
        "tone": schema_tone
    })
    return {
        "answer": answer.content.strip(),
        "resolution_note": resolution_note,
        "action": "DESCRIBE",
        "dax_attempts": [],
        "final_dax": "",
        "error": None,
    }

