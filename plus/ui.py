import streamlit as st
import streamlit.components.v1 as components
import json
from openai import OpenAI
from .config import load_config, save_config

def render_sidebar():
    st.header("🔧 设置")
    config = load_config()

    st.subheader("1. 数据库配置")
    td_host = st.text_input("TDengine Host", config.get("td_host", "localhost"))
    td_port = st.text_input("TDengine Port", config.get("td_port", "6041"))
    td_user = st.text_input("Username", config.get("td_user", "root"))
    td_pass = st.text_input("Password", config.get("td_pass", "taosdata"), type="password")

    st.subheader("2. AI 模型配置")
    api_key = st.text_input("API Key", value=config.get("api_key", ""), type="password")
    base_url = st.text_input("Base URL", config.get("base_url", "https://api.deepseek.com"))
    model_name = st.text_input("Model Name", config.get("model_name", "deepseek-chat"))

    st.subheader("3. 上下文记忆")
    mem = config.get("memory", {})
    station_code = st.text_input("station_code", mem.get("station_code", "gtjjlfgdzf"))
    equ_codes_str = st.text_input("equ_codes(逗号分隔)", ",".join(mem.get("equ_codes", [])))
    date_start = st.text_input("date_start", mem.get("date_start", ""))
    date_end = st.text_input("date_end", mem.get("date_end", ""))

    # 构造新的 config 对象（用于保存或返回）
    new_config = {
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
    }

    if st.button("🔌 测试 API 连接"):
        if not api_key:
            st.error("请先输入 API Key")
        else:
            try:
                client = OpenAI(api_key=api_key, base_url=base_url)
                # 尝试一个极简的请求
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )

                # 测试成功后自动保存配置
                save_config(new_config)
                st.success(f"✅ 连接成功！当前模型 '{model_name}' 可用。配置已保存。")
                # 更新当前内存中的 config，以便立即生效
                config.update(new_config)

            except Exception as e:
                st.error(f"❌ 连接失败\n\n**错误信息:** {str(e)}\n\n**排查建议:**\n1. 检查 Model Name 是否正确 (当前: `{model_name}`)\n2. 检查 Base URL 是否正确 (当前: `{base_url}`)\n3. 确认 API Key 是否有效")

    if st.button("💾 保存设置"):
        save_config(new_config)
        config.update(new_config)
        st.success("✅ 设置已保存")

    if st.button("🗑️ 清除聊天记录"):
        st.session_state.messages = []
        # 可选：是否也要清除上下文记忆？目前暂只清除显示的消息
        st.rerun()

    # 返回最新的配置
    return new_config

def show_applied_context(context):
    st.info(f"已应用上下文: station={context.get('station_code')}, equip={','.join(context.get('equ_codes', []))}, start={context.get('date_start')}, end={context.get('date_end')}")

def render_chart(df, chart_type="line"):
    """
    统一的图表渲染函数
    :param df: 数据 DataFrame
    :param chart_type: 'line', 'bar', 'area'
    """
    # 如果是窗口聚合查询，TDengine 返回 _wstart，统一重命名为 ts 以便绘图
    if "_wstart" in df.columns:
        df = df.rename(columns={"_wstart": "ts"})

    if "ts" in df.columns and len(df) > 1:
        # 清理列名中的特殊字符，避免 Altair 报错
        df.columns = [str(col).replace("(", "_").replace(")", "") for col in df.columns]

        numeric_cols = df.select_dtypes(include=["float", "int"]).columns
        # 排除非数值列或不需要绘图的列
        if len(numeric_cols) > 0:
            chart_data = df.set_index("ts")[numeric_cols]
            if chart_type == "bar":
                st.bar_chart(chart_data)
            elif chart_type == "area":
                st.area_chart(chart_data)
            else:
                st.line_chart(chart_data)

def inject_history_js(history_messages):
    """
    注入 JavaScript 以支持在 chat_input 中使用上下箭头回填历史记录
    """
    # 提取用户发送的消息内容
    user_history = [msg["content"] for msg in history_messages if msg.get("role") == "user"]

    js = f"""
    <script>
        (function() {{
            const history = {json.dumps(user_history)};
            let historyIndex = history.length;

            function setTextAreaValue(text) {{
                const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (textArea) {{
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                    nativeInputValueSetter.call(textArea, text);
                    textArea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                }}
            }}

            function init() {{
                const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                if (!textArea) {{
                    setTimeout(init, 500);
                    return;
                }}

                // 防止重复添加监听器 (简单检查)
                if (textArea.dataset.historyAttached === "true") return;
                textArea.dataset.historyAttached = "true";

                textArea.addEventListener('keydown', function(e) {{
                    if (e.key === 'ArrowUp') {{
                        if (historyIndex > 0) {{
                            historyIndex--;
                            setTextAreaValue(history[historyIndex]);
                        }}
                    }} else if (e.key === 'ArrowDown') {{
                        if (historyIndex < history.length) {{
                            historyIndex++;
                            const text = historyIndex === history.length ? "" : history[historyIndex];
                            setTextAreaValue(text);
                        }}
                    }}
                }});
            }}

            init();
        }})();
    </script>
    """
    components.html(js, height=0)
