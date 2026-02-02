import streamlit as st
from .config import load_config, save_config

def render_sidebar():
    st.header("设置")
    config = load_config()
    td_host = st.text_input("TDengine Host", config.get("td_host", "localhost"))
    td_port = st.text_input("TDengine Port", config.get("td_port", "6041"))
    td_user = st.text_input("Username", config.get("td_user", "root"))
    td_pass = st.text_input("Password", config.get("td_pass", "taosdata"), type="password")
    api_key = st.text_input("API Key", value=config.get("api_key", ""), type="password")
    base_url = st.text_input("Base URL", config.get("base_url", "https://api.deepseek.com"))
    model_name = st.text_input("Model Name", config.get("model_name", "deepseek-chat"))
    st.subheader("上下文记忆")
    mem = config.get("memory", {})
    station_code = st.text_input("station_code", mem.get("station_code", "gtjjlfgdzf"))
    equ_codes_str = st.text_input("equ_codes(逗号分隔)", ",".join(mem.get("equ_codes", [])))
    date_start = st.text_input("date_start", mem.get("date_start", ""))
    date_end = st.text_input("date_end", mem.get("date_end", ""))
    if st.button("保存设置"):
        config.update({
            "td_host": td_host,
            "td_port": td_port,
            "td_user": td_user,
            "td_pass": td_pass,
            "api_key": api_key,
            "base_url": base_url,
            "model_name": model_name,
            "memory": {
                "station_code": station_code,
                "equ_codes": [e.strip() for e in equ_codes_str.split(",") if e.strip()],
                "date_start": date_start,
                "date_end": date_end,
                "summary": mem.get("summary", ""),
                "recent_messages": mem.get("recent_messages", [])
            }
        })
        save_config(config)
        st.success("已保存")
    return config

def show_applied_context(context):
    st.info(f"已应用上下文: station={context.get('station_code')}, equip={','.join(context.get('equ_codes', []))}, start={context.get('date_start')}, end={context.get('date_end')}")
