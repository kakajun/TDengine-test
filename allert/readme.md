# 数据告警系统 (Data Alert System)

这是一个基于 Python 的高性能工业数据告警系统，旨在处理 CSV 格式或 **TDengine (TSDB)** 数据库的时序数据，支持基于规则的实时告警和机器学习模型辅助诊断。

## 🚀 技术栈

*   **语言**: Python 3.8+
*   **核心处理**: `pandas` (高性能向量化计算), `numpy`
*   **数据库连接**: `taosws-py` (TDengine WebSocket 连接)
*   **规则引擎**: `pandas.eval` / `numexpr` (支持复杂布尔表达式)
*   **机器学习**: `lightgbm` (优先), `scikit-learn` (RandomForest 作为回退), `joblib`
*   **CLI 工具**: `click`
*   **配置管理**: `PyYAML`
*   **日志**: `loguru`
*   **编码检测**: `chardet`

## ✨ 核心功能

1.  **多源数据加载 (Data Loader)**
    *   **CSV 支持**: 自动检测文件编码 (GBK/UTF-8)，支持 `PK` 和 `bit` 列解析。
    *   **TDengine 支持**: 通过 `taosws` 直接从数据库加载数据，支持自定义 SQL 查询。
    *   **字段映射**: 支持 JSON 格式 (`column_mapping.json`) 或 CSV 格式的列名映射，统一将数据库字段 (如 `wspd`) 映射为中文业务名称 (如 `风速`)。

2.  **向量化规则引擎 (Rule Engine)**
    *   支持使用中文列名编写规则表达式 (如 `支路电流 > 0.3 and 总辐照度 > 200`)。
    *   **时间窗口支持**: 支持 `5m any` (5分钟内任意触发), `10m all` (10分钟持续触发) 等逻辑。
    *   **告警去重**: 支持基于时间窗口的告警抑制 (Deduplication)，避免重复骚扰。

3.  **机器学习闭环 (Model Loop)**
    *   **数据合成**: 内置数据合成器，基于统计特征自动生成正负样本用于冷启动训练。
    *   **自动训练**: 集成 LightGBM/RandomForest，支持模型保存与加载。

## 📂 目录结构

```text
allert/                    # 源代码
├── configs/               # 配置文件目录
│   ├── config.yaml        # 系统主配置 (数据路径、输出路径等)
│   ├── rules.yaml         # 告警规则定义
│   └── test_config.yaml   # 测试配置
├── model/                 # 模型相关代码 (训练、合成)
├── alert_runner.py        # [入口] CLI 主程序
├── data_loader.py         # 数据加载与预处理 (支持 CSV/TSDB)
├── mapping_loader.py      # 列名映射加载 (支持 JSON/CSV)
└── rule_engine.py         # 规则引擎核心
out/                       # 输出目录 (告警结果、模型文件)
```

## 🛠️ 安装说明

1.  **环境准备**
    建议使用 Conda 创建独立环境：
    ```bash
    conda create -n alert_sys python=3.9
    conda activate alert_sys
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

## 📖 使用指南

### 1. 配置文件

在 `configs/config.yaml` 中配置数据映射和规则路径：

```yaml
data:
  input_pattern: "*.csv"
  # 映射文件路径，支持 JSON 格式
  mapping_path: "d:\\git\\TDengine-test\\column_mapping.json"
  mapping_encoding: "utf-8"

rules:
  path: "configs/rules.yaml"

output:
  path: "out/alerts.csv"
```

在 `configs/rules.yaml` 中定义告警规则：

```yaml
- name: 支路电流异常
  expr: 支路电流 < 0.3 and 总辐照度 > 200
  severity: high
  window: 5m any
  dedup: 10m
  message: "支路电流偏低，请检查"
```

### 2. 运行告警分析

使用 `run` 命令执行分析。系统支持两种模式：CSV 文件模式和数据库模式。

#### 模式一：从 TDengine 数据库加载 (推荐)

如果不指定 `--input`，系统将默认连接本地 TDengine 数据库。

```bash
# 使用默认 SQL 查询 (SELECT * FROM station_data.stable_gtjjlfgdzf LIMIT 1000)
python -m allert.alert_runner run

# 自定义 SQL 查询
python -m allert.alert_runner run --sql "SELECT * FROM station_data.stable_gtjjlfgdzf WHERE ts > NOW - 1d LIMIT 5000"
```

#### 模式二：从 CSV 文件加载

```bash
# 指定输入文件
python -m allert.alert_runner run --input your_data.csv

# 指定配置文件
python -m allert.alert_runner run --config configs/config.yaml --input your_data.csv
```

运行后，结果将保存在 `out/alerts.csv` (或配置中指定的路径)。

### 3. 训练模型 (Demo)

使用 `train-model` 命令基于输入数据合成样本并训练分类模型：

```bash
python -m allert.alert_runner train-model --config configs/config.yaml --input your_data.csv
```

## 🧪 开发与扩展

*   **添加新规则**: 直接修改 `rules.yaml`，无需重启代码。
*   **字段映射**: 如果数据库结构变更，请重新生成 `column_mapping.json`。
*   **扩展模型**: 在 `allert/model/` 下继承 `BaseModel` 实现新算法。
