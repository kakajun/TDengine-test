from openai import OpenAI
import re

def estimate_tokens(text):
    return max(1, len(text) // 4)

def build_schema_info(columns_desc, context):
    station = context.get("station_code") or "gtjjlfgdzf"
    equ = ",".join(context.get("equ_codes", [])) or "F01"
    ds = context.get("date_start") or ""
    de = context.get("date_end") or ""
    info = f"""
    Database: station_data
    Super Table: stable_gtjjlfgdzf
    Columns:
{columns_desc}
    Tags:
      - station_code (NCHAR): 场站编号
      - equ_code (NCHAR): 设备编号

    当前上下文
      - station_code: {station}
      - equ_codes: {equ}
      - date_start: {ds}
      - date_end: {de}
    """
    return info

def build_system_prompt(schema_info):
    return f"""
    你是一个 TDengine SQL 专家。你的任务是将用户的自然语言查询转换为 TDengine SQL 语句。

    【数据库结构】
    {schema_info}

    【重要提示】
    1. 必须严格根据【数据库结构】中的 Columns 描述来选择列名。
    2. 用户的查询词汇可能不完全匹配列描述，请根据语义选择最接近的列。例如 "有功" -> "发电机有功功率" (dc)。
    3. 如果有多个相似的列，优先选择描述最精准匹配的列。

    【TDengine 特有语法规则】
    1. 时间窗口聚合使用 INTERVAL(...) 语法，通常配合 WHERE ts >= ...。
    2. 获取最新数据使用 ORDER BY ts DESC LIMIT 1 或 LAST_ROW()。
    3. 字符串值需要用单引号。
    4. 禁止使用 AS 重命名列。

    【输出要求】
    仅输出 SQL 语句，不要包含 markdown 标记或解释文字。
    """

def clean_sql(sql):
    sql = sql.strip()
    sql = re.sub(r'^```sql\s*', '', sql)
    sql = re.sub(r'^```\s*', '', sql)
    sql = re.sub(r'\s*```$', '', sql)
    return sql

def generate_sql(user_query, api_key, base_url, model_name, schema_info):
    client = OpenAI(api_key=api_key, base_url=base_url)
    system_prompt = build_system_prompt(schema_info)
    resp = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0
    )
    sql = resp.choices[0].message.content
    return clean_sql(sql)
