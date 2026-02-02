import streamlit as st
import pandas as pd
from .config import load_config, save_config
from .memory import init_dialog_state, get_persistent_memory, set_persistent_memory, maybe_summarize_history
from .context import parse_query_slots, merge_with_memory
from .mapping import load_mapping, get_relevant_columns
from .llm import build_schema_info, generate_sql
from .db import execute_query
from .ui import render_sidebar, show_applied_context

st.set_page_config(page_title="光伏数据 AI 助手 Plus", page_icon="☀️", layout="wide")
if "messages" not in st.session_state:
    st.session_state.messages = []
init_dialog_state()

with st.sidebar:
    config = render_sidebar()

api_key = config.get("api_key", "")
base_url = config.get("base_url", "https://api.deepseek.com")
model_name = config.get("model_name", "deepseek-chat")
td_host = config.get("td_host", "localhost")
td_port = config.get("td_port", "6041")
td_user = config.get("td_user", "root")
td_pass = config.get("td_pass", "taosdata")
database = "station_data"

mapping = load_mapping()

st.title("☀️ 光伏场站数据智能助手 Plus")
for msg in st.session_state.messages:
    with st.chat_message(msg.get("role", "assistant")):
        st.markdown(msg.get("content", ""))
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "data" in msg:
            df = msg["data"]
            st.dataframe(df)
            if "ts" in df.columns and len(df) > 1:
                numeric_cols = df.select_dtypes(include=["float", "int"]).columns
                if len(numeric_cols) > 0:
                    st.line_chart(df.set_index("ts")[numeric_cols])

if prompt := st.chat_input("请输入您的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    slots = parse_query_slots(prompt)
    mem = get_persistent_memory(config)
    context = merge_with_memory(slots, st.session_state.dialog_state, mem)
    st.session_state.dialog_state.update(context)
    mem = set_persistent_memory(config, context)
    config = save_config(mem) or load_config()
    cols, desc = get_relevant_columns(prompt, context, mapping, k=40)
    schema_info = build_schema_info(desc, context)
    sql = generate_sql(prompt, api_key, base_url, model_name, schema_info)
    df = execute_query(sql, td_host, td_port, td_user, td_pass, database, mapping)
    with st.chat_message("assistant"):
        show_applied_context(context)
        st.code(sql, language="sql")
        st.dataframe(df)
        if "ts" in df.columns and len(df) > 1:
            numeric_cols = df.select_dtypes(include=["float", "int"]).columns
            if len(numeric_cols) > 0:
                st.line_chart(df.set_index("ts")[numeric_cols])
    st.session_state.messages.append({"role": "assistant", "content": "查询完成。", "sql": sql})
    config = maybe_summarize_history(load_config(), api_key, base_url, model_name)
