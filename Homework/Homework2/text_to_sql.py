# text_to_sql.py
# Usage:
#   python text_to_sql.py --schema schema.sql --question "Which customers spent the most last month?"
# or:
#   python text_to_sql.py --schema-text "CREATE TABLE ..." --question "..."
from dotenv import load_dotenv
load_dotenv()  # 自动读取项目根目录的 .env

import os
import argparse
from openai import OpenAI

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # change if you prefer another chat model

SYSTEM_PROMPT = """You are a precise Text-to-SQL generator.
- Input: (1) SQL dialect, (2) database schema (CREATE TABLE ...), (3) a natural-language question.
- Output: ONLY a valid SQL query that can run directly against the provided schema.
- Do NOT include explanations or markdown fences.
- Prefer ANSI SQL; if dialect is provided, follow it.
- Use only tables/columns that exist in the schema.
- If aggregation or filtering is ambiguous, choose the most reasonable interpretation.
"""

USER_TEMPLATE = """SQL Dialect: {dialect}

SCHEMA:
{schema}

QUESTION:
{question}

Return ONLY the SQL query, nothing else.
"""

def generate_sql(schema_text: str, question: str, dialect: str = "ANSI SQL", model: str = DEFAULT_MODEL, temperature: float = 0.1) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Please set the OPENAI_API_KEY environment variable.")

    client = OpenAI(api_key=api_key)

    user_msg = USER_TEMPLATE.format(dialect=dialect, schema=schema_text.strip(), question=question.strip())

    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg}
        ]
    )
    # Extract the assistant's message text
    sql = resp.choices[0].message.content.strip()
    return sql

def main():
    parser = argparse.ArgumentParser(description="Text-to-SQL via OpenAI Chat Completions")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--schema", type=str, help="Path to a .sql file containing CREATE TABLE statements")
    src.add_argument("--schema-text", type=str, help="Raw SQL schema text (CREATE statements) passed directly")
    parser.add_argument("--question", required=True, type=str, help="Natural-language question about the data")
    parser.add_argument("--dialect", default="ANSI SQL", help="SQL dialect hint (e.g., 'PostgreSQL', 'SQLite', 'MySQL')")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="OpenAI chat model (defaults to env OPENAI_MODEL or gpt-4o-mini)")
    parser.add_argument("--temperature", default=0.1, type=float, help="Sampling temperature (lower = more deterministic)")
    args = parser.parse_args()

    if args.schema:
        with open(args.schema, "r", encoding="utf-8") as f:
            schema_text = f.read()
    else:
        schema_text = args.schema_text

    sql = generate_sql(schema_text=schema_text, question=args.question, dialect=args.dialect, model=args.model, temperature=args.temperature)
    print(sql)

if __name__ == "__main__":
    main()
