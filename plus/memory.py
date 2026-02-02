import streamlit as st
from openai import OpenAI

def init_dialog_state():
    if "dialog_state" not in st.session_state:
        st.session_state.dialog_state = {
            "station_code": None,
            "equ_codes": [],
            "date_start": None,
            "date_end": None,
            "metrics": [],
            "agg": None
        }

def get_persistent_memory(config):
    return config.get("memory", {})

def set_persistent_memory(config, memory):
    config["memory"] = memory
    return config

def summarize_history(messages, api_key, base_url, model_name):
    if not api_key:
        return None
    client = OpenAI(api_key=api_key, base_url=base_url)
    text = ""
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        text += f"{role}: {content}\n"
    try:
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "请将以下对话浓缩为简短摘要，保留意图、站点、设备、时间范围与指标信息。"},
                {"role": "user", "content": text}
            ],
            temperature=0,
            max_tokens=256
        )
        return resp.choices[0].message.content.strip()
    except:
        return None

def maybe_summarize_history(config, api_key, base_url, model_name, count_threshold=8, char_threshold=5000):
    msgs = st.session_state.get("messages", [])
    total_chars = sum(len(m.get("content", "")) for m in msgs)
    if len(msgs) > count_threshold or total_chars > char_threshold:
        s = summarize_history(msgs[:-4], api_key, base_url, model_name)
        mem = get_persistent_memory(config)
        if s:
            mem["summary"] = s
            config = set_persistent_memory(config, mem)
        st.session_state["messages"] = mem.get("recent_messages", msgs[-4:])
        return config
    return config
