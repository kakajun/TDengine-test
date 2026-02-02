我将改造 `allert` 工程，使其对接 TDengine 数据库和 JSON 映射文件。

### 1. 修改 `allert/mapping_loader.py`
- 更新 `load_mapping` 方法，使其支持读取 `column_mapping.json` 文件。
- 解析简单的键值对结构（如 `{"a": "有功功率"}`），替代原有的 CSV 解析逻辑。

### 2. 修改 `allert/data_loader.py`
- 引入 `taosws` 依赖。
- 新增 `load_from_tsdb(self, sql)` 方法：
  - 使用 `taosws` 连接本地 TDengine。
  - 执行 SQL 查询（默认为 `SELECT * FROM station_data.stable_gtjjlfgdzf LIMIT 1000`）。
  - 将结果转换为 Pandas DataFrame。
  - **标准化处理**:
    - 将 `ts` 列设为时间索引。
    - 将 `equ_code` 重命名为 `device_id`（适配原系统逻辑）。
    - 调用 MappingLoader 将物理列名（如 `a`, `aa`）转换为中文业务名称。

### 3. 修改 `allert/alert_runner.py`
- 改造 `run` 命令：
  - 移除对 CSV 输入文件的强制依赖。
  - 增加从数据库加载数据的逻辑。

### 4. 更新配置文件
- 修改 `configs/config.yaml`，将映射文件路径更新为 `d:\git\TDengine-test\column_mapping.json`。
