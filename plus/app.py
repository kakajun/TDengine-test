import streamlit as st
import pandas as pd
import sys
import os

# 将项目根目录添加到 sys.path 以便导入 plus 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from plus.config import load_config, save_config
from plus.memory import init_dialog_state, get_persistent_memory, set_persistent_memory, maybe_summarize_history
from plus.context import parse_query_slots, merge_with_memory
from plus.mapping import load_mapping, get_relevant_columns
from plus.llm import build_schema_info, generate_sql
from plus.db import execute_query
from plus.ui import render_sidebar, show_applied_context, render_chart, inject_history_js

st.set_page_config(page_title="光伏数据 AI 助手 Plus", page_icon="☀️", layout="wide")
if "messages" not in st.session_state:
    st.session_state.messages = []
init_dialog_state()

with st.sidebar:
    config = render_sidebar()

# 注入历史记录回填脚本
inject_history_js(st.session_state.messages)

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
st.markdown(
    "直接输入问题，例如：*“查询 F01 设备 2026-01-28 一整天的发电机有功功率 曲线”* 或 *“查询 gtjjlfgdzf 2026-01-28 一整天的风速, 线图”*")

for msg in st.session_state.messages:
    with st.chat_message(msg.get("role", "assistant")):
        st.markdown(msg.get("content", ""))
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "data" in msg:
            df = msg["data"]
            st.dataframe(df)
            render_chart(df, msg.get("chart_type", "line"))

if prompt := st.chat_input("请输入您的问题..."):
    # Print user query to console
    print(f"\n{'='*50}\n[User Query]: {prompt}\n{'='*50}")

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

    # Print generated SQL to console
    print(f"\n[Generated SQL]:\n{sql}\n{'-'*50}")

    df = execute_query(sql, td_host, td_port, td_user, td_pass, database, mapping)

    # Determine chart type
    chart_type = "line"
    if "柱" in prompt:
        chart_type = "bar"
    elif "面积" in prompt:
        chart_type = "area"

    with st.chat_message("assistant"):
        show_applied_context(context)
        st.code(sql, language="sql")
        st.dataframe(df)
        render_chart(df, chart_type)

    st.session_state.messages.append({
        "role": "assistant",
        "content": "查询完成。",
        "sql": sql,
        "data": df,
        "chart_type": chart_type
    })
    config = maybe_summarize_history(load_config(), api_key, base_url, model_name)
