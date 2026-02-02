# ☀️ 光伏数据 AI 查询助手 (Solar AI Bot)

本项目基于 **TDengine** 和 **大语言模型 (LLM)**，让您可以通过自然语言（聊天）的方式查询光伏场站的发电数据，并自动生成图表。

## 🚀 快速开始

### 第一步：环境准备 (最重要！)

1.  **安装 TDengine 数据库**
    *   请务必先阅读并按照 [SETUP_GUIDE.md](SETUP_GUIDE.md) 中的步骤安装 TDengine。
    *   确保数据库服务已启动（端口 6041 可用）。

2.  **验证环境**
    *   运行以下命令检查数据库连接：
    ```bash
    python check_env.py
    ```
    *   如果看到 "✅ 连接成功"，请继续。如果失败，请检查 TDengine 安装。

### 第二步：安装 Python 依赖

在项目根目录下运行：
```bash
pip install -r requirements.txt
```

### 第三步：生成模拟数据

为了让系统有数据可查，我们需要先生成一些模拟的光伏历史数据：
```bash
python data_generator.py
```
*   成功后会提示“数据生成完成”。

### 第四步：启动应用

运行以下命令启动网页界面：
```bash
streamlit run app.py
```
*   系统会自动打开浏览器，访问 `http://localhost:8501`。

---
## 启动
docker start taosdb-ee

## 💡 如何使用

1.  **配置设置** (左侧侧边栏)：
    *   **数据库配置**：默认通常不需要修改 (localhost:6041)。
    *   **AI 模型配置**：输入您的 API Key（如 OpenAI, DeepSeek, 智谱 AI 等）。
        *   如果是 **DeepSeek**：
            *   Base URL 填: `https://api.deepseek.com`
            *   Model Name 填: `deepseek-chat` (或者 `deepseek-reasoner`)
        *   如果是 Moonshot，Base URL 填 `https://api.moonshot.cn/v1`。

2.  **开始提问**：
    *   在对话框输入问题，例如：
        *   "Station_A 今天的总发电量是多少？"
        *   "Station_B 过去 7 天的功率曲线"
        *   "对比 Station_A 和 Station_B 昨天的日发电量"

3.  **查看结果**：
    *   AI 会自动生成 SQL 并查询数据库。
    *   如果是趋势类数据，系统会自动绘制折线图。
