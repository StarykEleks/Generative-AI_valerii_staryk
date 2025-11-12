import os, sqlite3, json, logging, datetime as dt, requests
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "b.db"))
os.makedirs(os.path.join(os.path.dirname(__file__), "tickets"), exist_ok=True)

logger = logging.getLogger("tools")
logger.setLevel(logging.INFO)

BLOCKLIST = ["DROP","DELETE","TRUNCATE","ALTER","INSERT","UPDATE","REPLACE","ATTACH","DETACH","VACUUM","PRAGMA"]

schema = ("""
    table: book_reviews
    columns: book_id (text), reviewer_id (text), reviewer_name (text),likes_on_review (text), review_content (text), reviewer_followers (text), reviewer_total_reviews (text), review_date (text), review_rating (text)
    
    table: books
    columns: id (integer), title (text), total_books (integer), total_votes (integer)
""")


def is_safe_sql(q: str) -> bool:
    u = q.upper()
    return not any(w in u for w in BLOCKLIST)

def connect_ro(db_path: str):
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)

def tool_query_db(sql: str, max_rows: int = 500) -> Dict[str, Any]:
    logger.info(f"query_db SQL:\n{sql}")
    if not is_safe_sql(sql):
        return {"error": "Unsafe SQL detected. Only read-only SELECT queries are allowed."}
    try:
        con = connect_ro(DB_PATH)
        cur = con.cursor()
        cur.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall()[:max_rows]
        con.close()
        logger.info(f"query_db returned {len(rows)} rows")
        return {"columns": cols, "rows": rows, "row_count": len(rows)}
    except Exception as e:
        logger.exception("DB error")
        return {"error": str(e)}

def tool_get_dataset_overview() -> Dict[str, Any]:
    try:
        con = connect_ro(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM books")
        books = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM book_reviews")
        reviews = cur.fetchone()[0]
        con.close()
        return {"books": books, "book_reviews": reviews}
    except Exception as e:
        logger.exception("overview error")
        return {"error": str(e)}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

def tool_create_support_ticket(title: str, body: str) -> Dict[str, Any]:
    logger.info(f"create_support_ticket: {title}")
    if GITHUB_TOKEN and GITHUB_REPO:
        try:
            r = requests.post(
                f"https://api.github.com/repos/StarykEleks/{GITHUB_REPO}/issues",
                headers={"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"},
                json={"title": title, "body": body}
            )
            if 200 <= r.status_code < 300:
                data = r.json()
                return {"status":"created","provider":"github","issue_number":data.get("number"),"html_url":data.get("html_url")}
            return {"status":"error","provider":"github","details":r.text}
        except Exception as e:
            return {"status":"error","provider":"github","details":str(e)}

def get_tools_schema() -> List[dict]:
    return [
        {
            "type":"function",
            "function": {
                "name": "query_db",
                "description": f""" 
                            Get the answer from the SQL database based on a query
                            SQL should be written using database schema {schema}""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string"},
                    },
                    "required": ["sql"]}
            },
        },
        {"type":"function","function":{"name":"create_support_ticket","description":"Create a support ticket (GitHub if configured; otherwise local).","parameters":{"type":"object","properties":{"title":{"type":"string"},"body":{"type":"string"}},"required":["title","body"]}}}
    ]

