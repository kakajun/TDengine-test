import streamlit as st
import pandas as pd
import taosws
from openai import OpenAI
import json
import re
import os

# --- 加载字段映射 ---
MAPPING_FILE = "db_column_mapping.json"
COLUMN_MAPPING = {}
if os.path.exists(MAPPING_FILE):
    try:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            COLUMN_MAPPING = json.load(f)
    except Exception as e:
        st.error(f"加载字段映射失败: {e}")
else:
    st.warning("未找到字段映射文件 db_column_mapping.json")

# --- 配置文件管理 ---
CONFIG_FILE = "config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_config(config):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        st.error(f"保存配置失败: {e}")


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

    # 加载配置
    config = load_config()

    st.subheader("1. 数据库配置")
    td_host = st.text_input(
        "TDengine Host", config.get("td_host", "localhost"))
    td_port = st.text_input("TDengine Port", config.get("td_port", "6041"))
    td_user = st.text_input("Username", config.get("td_user", "root"))
    td_pass = st.text_input("Password", config.get(
        "td_pass", "taosdata"), type="password")

    st.subheader("2. AI 模型配置")
    api_key = st.text_input("API Key", value=config.get("api_key", ""), type="password",
                            help="请输入您的 OpenAI/DeepSeek 等模型的 API Key")
    base_url = st.text_input("Base URL", config.get("base_url", "https://api.deepseek.com"),
                             help="例如 DeepSeek 使用: https://api.deepseek.com")
    model_name = st.text_input(
        "Model Name", config.get("model_name", "deepseek-chat"), help="DeepSeek 填: deepseek-chat; OpenAI 填: gpt-4o")

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

                # 保存配置
                save_config({
                    "td_host": td_host,
                    "td_port": td_port,
                    "td_user": td_user,
                    "td_pass": td_pass,
                    "api_key": api_key,
                    "base_url": base_url,
                    "model_name": model_name
                })

                st.success(f"✅ 连接成功！当前模型 '{model_name}' 可用。配置已保存。")
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
        cursor.execute("USE station_data")

        cursor.execute(sql)
        fields = [field[0] for field in cursor.description]
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        df = pd.DataFrame(data, columns=fields)

        # 重命名列 (如果存在映射)
        if COLUMN_MAPPING:
            # 仅重命名存在于映射中的列
            rename_dict = {k: v for k,
                           v in COLUMN_MAPPING.items() if k in df.columns}
            if rename_dict:
                df = df.rename(columns=rename_dict)

        return df, None
    except Exception as e:
        return None, str(e)


def get_sql_from_llm(user_query):
    if not api_key:
        return None, "请先在左侧侧边栏设置 API Key"

    client = OpenAI(api_key=api_key, base_url=base_url)

    # 定义 Schema 和 Prompt
    # 动态生成字段描述
    columns_desc = ""
    # 为了避免 Context 溢出，如果字段太多，只选取一部分关键字段或者精简描述
    # 这里我们列出所有字段，但格式紧凑
    for col, desc in COLUMN_MAPPING.items():
        columns_desc += f"      - {col} (DOUBLE): {desc}\n"

    schema_info = f"""
    Database: station_data
    Super Table: stable_gtjjlfgdzf
    Columns:
      - ts (TIMESTAMP): 时间戳
{columns_desc}
    Tags:
      - station_code (NCHAR): 场站编号 (例如 'gtjjlfgdzf')
      - equ_code (NCHAR): 设备编号 (例如 'F15', 'F24')

    【数据时间范围】
    - 数据起始时间: 2026-01-22 12:32:00
    - 数据结束时间: 2026-01-28 16:00:00
    - 注意：如果用户查询"今天"或"最新"的数据，请优先关注 2026-01-28 附近的数据，或者明确告知用户当前数据的时间范围。

    【TDengine 特有语法规则】
    你是一个 TDengine SQL 专家。你的任务是将用户的自然语言查询转换为 TDengine SQL 语句。

    【数据库结构】
    {schema_info}

    【TDengine 特有语法规则】
    1. 时间窗口聚合使用 `INTERVAL(1h)` 或 `INTERVAL(1d)` 等语法，通常配合 `WHERE ts >= ...` 使用。
    2. 获取最新数据使用 `ORDER BY ts DESC LIMIT 1` 或 `LAST_ROW()` 函数。
    3. 今天的范围是 `ts >= TODAY`，过去24小时是 `ts >= NOW - 24h`。
    4. 降采样查询（如曲线图）必须包含时间戳列 `ts`。
    5. 注意字符串值需要用单引号包裹。
    6. 禁止使用 AS 关键字重命名列，直接使用原始列名（例如使用 `select av` 而不是 `select av AS '1_有功功率'`），列名重命名由前端自动处理。

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
st.markdown(
    "直接输入问题，例如：*“查询 F15 设备 2026-01-28 的 1_PV9输入电流 曲线”* 或 *“查询 gtjjlfgdzf 场站 F16 设备最新的 1_有功功率”*")

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
