import os, sqlite3, json, logging, datetime as dt, requests
from typing import Any, Dict, List
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", os.path.join(os.path.dirname(__file__), "data", "books.db"))
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
        cur.execute("""
            SELECT b.title, ROUND(AVG(CAST(br.review_rating AS REAL)),2) AS avg_rating, COUNT(*) AS n
            FROM book_reviews br JOIN books b ON b.id = CAST(br.book_id AS INTEGER)
            GROUP BY b.title HAVING n >= 5 ORDER BY avg_rating DESC, n DESC LIMIT 10
        """ )
        top_books = cur.fetchall()
        cur.execute("""
            SELECT substr(review_date,1,7) AS ym, COUNT(*) FROM book_reviews GROUP BY ym ORDER BY ym
        """ )
        monthly = cur.fetchall()
        con.close()
        return {"books": books, "book_reviews": reviews, "top_books": top_books, "reviews_by_month": monthly}
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
    ticket = {"id": f"local-{dt.datetime.utcnow().isoformat()}".replace(":","-"),
              "title": title, "body": body, "created_at": dt.datetime.utcnow().isoformat()+"Z", "provider":"local"}
    path = os.path.join(os.path.dirname(__file__), "tickets", f"{ticket['id']}.json")
    with open(path,"w") as f: json.dump(ticket, f, indent=2)
    return {"status":"created","provider":"local","path": path}

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

def local_intent_router(message: str):
    m = message.lower()
    if any(k in m for k in ["ticket","support","human","issue"]):
        return ("create_support_ticket", {"title":"User requested support", "body": message})
    if "select" in m:
        return ("query_db", {"sql": message})
    if "rating distribution" in m:
        sql = """
        SELECT review_rating AS rating, COUNT(*) AS n
        FROM book_reviews
        GROUP BY review_rating ORDER BY CAST(review_rating AS INTEGER);
        """
        return ("query_db", {"sql": sql})
    return ("get_dataset_overview", {})
