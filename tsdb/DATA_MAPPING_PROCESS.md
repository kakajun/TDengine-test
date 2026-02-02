# TDengine 数据字段映射与应用改造记录

本文档记录了将原始 CSV 业务元数据映射到 TDengine 数据库字段，并改造 Streamlit 应用 (`app2.py`) 以支持自然语言查询的全过程。

## 1. 背景与目标
- **数据源**: `靳家梁.csv` (包含风机数据的测点定义，如 `chinese_name` 对应中文描述，`index` 对应数据库列索引)。
- **数据库**: TDengine `station_data` 库，超级表 `stable_gtjjlfgdzf`。
- **目标**:
  1. 建立 CSV 业务字段与 TDengine 物理列名的映射关系。
  2. 改造 `app2.py`，使其能利用这些映射关系，让 LLM 理解每个列（如 `aa`, `ab`）的实际物理含义（如“发电机定子温度”）。
  3. 优化用户体验，包括配置持久化和真实的查询时间范围。

## 2. 详细步骤

### 第一步：数据源分析与验证
首先分析了 `靳家梁.csv` 的结构，发现 `turbineName` 为 `G16` 的行包含了完整的点表信息。
- **关键字段**:
  - `index`: 对应 TDengine 的列名（如 `A`, `AA`, `AB`...）。
  - `chinese_name`: 对应字段的中文描述（如“有功功率”，“风速”）。
- **验证**:
  - 编写脚本验证了 TDengine 表 `stable_gtjjlfgdzf` 的列结构，确认其列名（`a`, `aa`, `ab`...）与 CSV 中的 `index` 是一一对应的（忽略大小写）。

### 第二步：生成映射文件
编写了 Python 脚本 `generate_mapping.py` 来自动化提取映射关系。

**脚本逻辑**:
1. 读取 `靳家梁.csv`。
2. 过滤 `turbineName == 'G16'` 的数据。
3. 遍历每一行，提取 `index`（转为小写）作为键，`chinese_name` 作为值。
4. 使用正则表达式 `^[a-zA-Z]+$` 确保只提取字母类型的列索引（排除非列名数据）。
5. 将结果保存为 `db_column_mapping.json`。

**产物**: `db_column_mapping.json`
```json
{
  "a": "有功功率",
  "aa": "风向",
  "ab": "机舱温度",
  ...
}
```

### 第三步：应用改造 (app2.py)
对 `app2.py` 进行了核心改造，使其能够动态加载映射并生成准确的 SQL。

#### 1. 动态加载映射
在应用启动时读取 `db_column_mapping.json`：
```python
MAPPING_FILE = "db_column_mapping.json"
if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r") as f:
        COLUMN_MAPPING = json.load(f)
```

#### 2. 注入 Prompt 上下文
将加载的映射表格式化为字符串，注入到发给 LLM 的 System Prompt 中。这样 LLM 就能知道用户问“风速”时，应该查询 `aa` 列。
```python
# 动态生成字段描述
columns_desc = []
for col, desc in COLUMN_MAPPING.items():
    columns_desc.append(f"- {col}: {desc}")
schema_info = "\n".join(columns_desc)
```

#### 3. 数据库连接与查询优化
- 将数据库连接目标从 `solar_power` 修改为 `station_data`。
- 查询表改为 `stable_gtjjlfgdzf`。
- **Prompt 优化**: 明确禁止 LLM 在 SQL 中使用 `AS` 别名（如 `SELECT avg(a) AS avg_power`），因为 TDengine REST API 对别名支持可能导致解析问题，直接返回原始列名更稳定。
- **时间范围**: 查询了数据库的实际时间范围（2023-06-01 到 2023-06-10），并在 Prompt 中提示 LLM 默认查询此范围的数据。

### 第四步：用户体验优化
为了方便测试，增加了配置持久化功能。
- **Config 管理**: 创建 `load_config` 和 `save_config` 函数。
- **自动保存**: 当用户在侧边栏测试 API 连接成功后，自动将 API Key、Base URL 和 TDengine 配置保存到 `config.json`。
- **自动加载**: 应用启动时自动填充上次的配置。

## 3. 最终效果
用户现在可以在 `app2.py` 中输入自然语言，例如：“查询 2023年6月1日 风速大于 5 的数据”，LLM 会自动将其转换为：
```sql
SELECT * FROM stable_gtjjlfgdzf WHERE ts >= '2023-06-01 00:00:00' AND aa > 5 LIMIT 10;
```
（其中 `aa` 被正确识别为“风速”）。
