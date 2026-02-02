import streamlit as st
import pandas as pd
import taosws
from openai import OpenAI
import json
import re

# --- 页面配置 ---
st.set_page_config(
    page_title="光伏数据 AI 助手",
    page_icon="☀️",
    layout="wide"
)

# --- 初始化 Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar: 配置 ---
with st.sidebar:
    st.header("🔧 设置")

    st.subheader("1. 数据库配置")
    td_host = st.text_input("TDengine Host", "localhost")
    td_port = st.text_input("TDengine Port", "6041")
    td_user = st.text_input("Username", "root")
    td_pass = st.text_input("Password", "taosdata", type="password")

    st.subheader("2. AI 模型配置")
    api_key = st.text_input("API Key", type="password",
                            help="请输入您的 OpenAI/DeepSeek 等模型的 API Key")
    base_url = st.text_input("Base URL", "https://api.deepseek.com",
                             help="例如 DeepSeek 使用: https://api.deepseek.com")
    model_name = st.text_input(
        "Model Name", "deepseek-chat", help="DeepSeek 填: deepseek-chat; OpenAI 填: gpt-4o")

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
                st.success(f"✅ 连接成功！当前模型 '{model_name}' 可用。")
            except Exception as e:
                st.error(
                    f"❌ 连接失败\n\n**错误信息:** {str(e)}\n\n**排查建议:**\n1. 检查 Model Name 是否正确 (当前: `{model_name}`)\n2. 检查 Base URL 是否正确 (当前: `{base_url}`)\n3. 确认 API Key 是否有效")

    if st.button("清除聊天记录"):
        st.session_state.messages = []
        st.rerun()

# --- 核心函数 ---


def get_db_connection():
    dsn = f"taosws://{td_user}:{td_pass}@{td_host}:{td_port}"
    return taosws.connect(dsn)


def execute_query(sql):
    try:
        conn = get_db_connection()
        # 确保使用正确的数据库
        cursor = conn.cursor()
        cursor.execute("USE solar_power")

        cursor.execute(sql)
        fields = [field[0] for field in cursor.description]
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return pd.DataFrame(data, columns=fields), None
    except Exception as e:
        return None, str(e)


def get_sql_from_llm(user_query):
    if not api_key:
        return None, "请先在左侧侧边栏设置 API Key"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 定义 Schema 和 Prompt
    schema_info = """
    Database: solar_power
    Super Table: meters
    Columns:
      - ts (TIMESTAMP): 时间戳
      - current (FLOAT): 电流 (A)
      - voltage (FLOAT): 电压 (V)
      - power (FLOAT): 功率 (kW)
      - energy_daily (FLOAT): 当日累计发电量 (kWh)
    Tags:
      - location (BINARY): 场站名称 (例如 'Station_A', 'Station_B')
      - model (BINARY): 设备型号
    """

    system_prompt = f"""
    你是一个 TDengine SQL 专家。你的任务是将用户的自然语言查询转换为 TDengine SQL 语句。

    【数据库结构】
    {schema_info}

    【TDengine 特有语法规则】
    1. **核心规则 (INTERVAL)**：当使用 `INTERVAL` 进行时间窗口聚合（降采样）时，SELECT 列表中**绝对不能**包含 `ts` 列，必须使用 `_wstart`。
    2. **绘图要求**：为了让前端能画图，请务必将 `_wstart` 重命名为 `ts`。
       - ✅ 正确: `SELECT _wstart AS ts, avg(power) FROM meters ... INTERVAL(1h)`
       - ❌ 错误: `SELECT ts, avg(power) ... INTERVAL(1h)`
    3. **普通聚合**：如果没有 `INTERVAL`，SELECT 列表中**绝对不能**包含 `ts` 或 `_wstart`。
       - ✅ 正确: `SELECT avg(power) FROM meters ...`
       - ❌ 错误: `SELECT ts, avg(power) ...`
    4. 获取最新数据使用 `ORDER BY ts DESC LIMIT 1` 或 `LAST_ROW()`。
    5. 今天的范围是 `ts >= TODAY`，过去24小时是 `ts >= NOW - 24h`。
    6. 字符串值需要用单引号包裹。

    【输出要求】
    1. 仅输出 SQL 语句，不要包含 markdown 代码块标记（如 ```sql ... ```）。
    2. 不要输出任何解释性文字。
    """

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0
        )
        sql = response.choices[0].message.content.strip()
        # 清理可能存在的 markdown 标记
        sql = re.sub(r'^```sql\s*', '', sql)
        sql = re.sub(r'^```\s*', '', sql)
        sql = re.sub(r'\s*```$', '', sql)
        return sql, None
    except Exception as e:
        error_msg = f"AI 调用失败: {str(e)}\n\n(当前配置 -> Model: {model_name}, Base URL: {base_url})"
        return None, error_msg

# --- 主界面 ---


st.title("☀️ 光伏场站数据智能助手")
st.markdown("直接输入问题，例如：*“Station_A 今天的功率曲线是什么？”* 或 *“Station_B 昨天的总发电量”*")

# 展示历史消息
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sql" in msg:
            st.code(msg["sql"], language="sql")
        if "data" in msg:
            df = msg["data"]
            st.dataframe(df)
            # 自动绘图逻辑
            if "ts" in df.columns and len(df) > 1:
                # 寻找数值列
                numeric_cols = df.select_dtypes(
                    include=['float', 'int']).columns
                if len(numeric_cols) > 0:
                    st.line_chart(df.set_index("ts")[numeric_cols])

# 处理用户输入
if prompt := st.chat_input("请输入您的问题..."):
    # 1. 显示用户问题
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. 生成 SQL
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 正在思考 SQL...")

        sql, error = get_sql_from_llm(prompt)

        if error:
            message_placeholder.error(error)
            st.session_state.messages.append(
                {"role": "assistant", "content": f"❌ 错误: {error}"})
        else:
            message_placeholder.markdown(f"**生成的 SQL:**\n```sql\n{sql}\n```")

            # 3. 执行查询
            with st.spinner("正在查询数据库..."):
                df, db_error = execute_query(sql)

            if db_error:
                st.error(f"数据库查询失败: {db_error}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": f"数据库错误: {db_error}", "sql": sql})
            else:
                # 4. 展示结果
                st.success(f"查询成功！共找到 {len(df)} 条记录。")
                st.dataframe(df)

                # 尝试绘图
                if "ts" in df.columns and len(df) > 1:
                    numeric_cols = df.select_dtypes(
                        include=['float', 'int']).columns
                    if len(numeric_cols) > 0:
                        st.line_chart(df.set_index("ts")[numeric_cols])

                # 保存到历史记录 (这里简化，不保存 heavy dataframe 到 session state 以免卡顿，只保存 SQL)
                # 实际生产中可以优化
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "查询完成。",
                    "sql": sql,
                    # "data": df # 如果需要历史记录里也能重绘图表，需要保存 data
                })
