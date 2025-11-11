import os, json, logging
import streamlit as st
import pandas as pd
import altair as alt
from dotenv import load_dotenv

from tools import (
    tool_query_db, tool_get_dataset_overview, tool_create_support_ticket,
    get_tools_schema, local_intent_router
)

load_dotenv()

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(name)s: %(message)s')
logger = logging.getLogger("app")

USE_OPENAI = False
try:
    from openai import OpenAI
    if os.getenv("OPENAI_API_KEY"):
        client = OpenAI()
        USE_OPENAI = True
        logger.info("OpenAI client ready")
except Exception as e:
    logger.warning(f"OpenAI not available: {e}")

st.set_page_config(page_title="Books Insights App", page_icon="📚", layout="wide")
st.title("📚 Books Insights — Ask anything about your DB")
st.caption("Agent runs **safe, read-only SQL** with function calling. Create a support ticket if you need a human.")

if "chat" not in st.session_state: st.session_state.chat = []
if "logs" not in st.session_state: st.session_state.logs = []

def log_ui(m): st.session_state.logs.append(m); logger.info(m)

with st.sidebar:
    st.subheader("Dataset Overview")
    ov = tool_get_dataset_overview()
    if "error" in ov:
        st.error(ov["error"])
    else:
        col1, col2 = st.columns(2)
        col1.metric("Books", ov.get("books", 0))
        col2.metric("Reviews", ov.get("book_reviews", 0))
        if ov.get("reviews_by_month"):
            df_m = pd.DataFrame(ov["reviews_by_month"], columns=["ym","n"])
            ch = alt.Chart(df_m).mark_line(point=True).encode(x="ym:O", y="n:Q", tooltip=["ym","n"]).properties(height=160)
            st.altair_chart(ch, use_container_width=True)

st.markdown("## Ask the agent")
for role, content in st.session_state.chat:
    who = "🧑‍💻 You" if role == "user" else "🤖 Agent"
    st.markdown(f"**{who}:** {content}")

user_msg = st.text_input("Type a question or a SQL SELECT targeting your schema...", key="user_input")
colA, colB = st.columns(2)
with colA:
    btn_ticket = st.button("Need a human? Create support ticket", use_container_width=True)
with colB:
    btn_clear = st.button("Clear chat", use_container_width=True)

if btn_clear:
    st.session_state.chat = []
    st.rerun()

def run_tool_call(name: str, arguments: dict):
    if name == "query_db":
        res = tool_query_db(**arguments)
        if "error" in res:
            st.error(res["error"]); log_ui(f"query_db error: {res['error']}"); return
        df = pd.DataFrame(res["rows"], columns=res.get("columns", [])) if res.get("columns") else pd.DataFrame()
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=300)
            cols = set(df.columns.str.lower())
            if {"ym","n"}.issubset(cols):
                st.altair_chart(alt.Chart(df).mark_line(point=True).encode(x="ym:O", y="n:Q", tooltip=list(df.columns)), use_container_width=True)
            if {"avg_rating","title"}.issubset(cols):
                st.altair_chart(alt.Chart(df).mark_bar().encode(x="title:N", y="avg_rating:Q", tooltip=list(df.columns)), use_container_width=True)
        st.success(f"Returned {res.get('row_count',0)} rows.")
        log_ui(f"query_db ok: {res.get('row_count',0)} rows")
    elif name == "create_support_ticket":
        res = tool_create_support_ticket(**arguments)
        if res.get("status") == "created" and res.get("provider") == "github" and res.get("html_url"):
            st.success(f"✅ GitHub issue created: {res['html_url']}")
        elif res.get("status") == "created" and res.get("provider") == "local" and res.get("path"):
            st.success(f"🗂️ Local ticket created at: {res['path']}")
        else:
            st.error(f"Ticket error: {res}")
        log_ui(f"create_support_ticket: {json.dumps(res)}")
    else:
        st.warning(f"Unknown tool: {name}"); log_ui(f"Unknown tool: {name}")

def agent_handle(message: str):
    st.session_state.chat.append(("user", message))
    st.markdown(f"**🧑‍💻 You:** {message}")
    log_ui(f"user_message: {message}")

    if USE_OPENAI:
        from openai import OpenAI
        client = OpenAI()
        tools = get_tools_schema()
        msgs = [{"role":"user","content":message}]
        resp = client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=msgs, tools=tools, tool_choice="auto", temperature=0.2
        )
        choice = resp.choices[0]
        tool_calls = getattr(choice.message, "tool_calls", None) or choice.message.tool_calls
        reply_text = getattr(choice.message, "content", None) or choice.message.content

        if tool_calls:
            for tc in tool_calls:
                name = tc.function.name
                import json as _json
                args = _json.loads(tc.function.arguments or "{}")
                st.session_state.chat.append(("assistant", f"Calling tool: {name} with {args}"))
                st.markdown(f"**🤖 Agent:** Calling `{name}` ...")
                run_tool_call(name, args)
        else:
            st.session_state.chat.append(("assistant", reply_text or "(no reply)"))
            st.markdown(f"**🤖 Agent:** {reply_text or '(no reply)'}")
    else:
        tool_name, args = local_intent_router(message)
        st.session_state.chat.append(("assistant", f"(local) calling {tool_name} with {args}"))
        st.markdown(f"**🤖 Agent:** (local) calling `{tool_name}` ...")
        run_tool_call(tool_name, args)

if user_msg:
    agent_handle(user_msg)

if btn_ticket:
    run_tool_call("create_support_ticket", {
        "title":"User asked for human assistance",
        "body":"Please follow up with the user regarding their books DB question."
    })

st.markdown("---")
with st.expander("Debug logs (last 50)"):
    for line in st.session_state.logs[-50:]:
        st.code(line)
