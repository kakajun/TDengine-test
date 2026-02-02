## 目标
- 将单文件 `app2.py` 重构为模块化工程，置于 `plus/` 文件夹，便于维护与扩展。
- 增强对话上下文与记忆能力（短期与持久）。
- 优化列映射注入（仅传 Top‑K 相关列），并加入上下文超限处理（滚动摘要+Schema 精简）。

## 目录与模块划分
- `plus/app.py`：Streamlit 入口（原 `app2.py` 主体），整合各模块。
- `plus/config.py`：加载/保存配置（沿用 `config.json`，新增 memory 字段）。
- `plus/memory.py`：`DialogState` 管理，短期会话与持久记忆（滚动摘要）。
- `plus/context.py`：槽位抽取（站点/设备/时间/指标）与与历史合并。
- `plus/mapping.py`：映射加载（`column_mapping.json` 优先，`db_column_mapping.json` 备选）、同义词与 Top‑K 相关列筛选。
- `plus/llm.py`：Prompt 构建、SQL 生成、历史摘要生成、token 预算估算与降级。
- `plus/db.py`：TDengine 连接与查询、结果重命名（按映射）。
- `plus/ui.py`：Sidebar 上下文字段编辑与主区提示/绘图。
- `plus/utils.py`：通用函数（正则、token 预算估算等）。

## 启动与路径
- 启动命令：`streamlit run plus/app.py`
- 依赖不变（使用现有 `requirements.txt`）。
- 不新增文档文件；持久记忆复用 `config.json` 的 `memory` 字段。

## 实施步骤
1. **抽取配置与记忆**：
   - 将现有 `load_config`/`save_config` 移至 `config.py`；新增 `memory` 读写（摘要、最近上下文）。
2. **对话记忆与槽位**：
   - 在 `memory.py` 添加 `DialogState`（session）与持久记忆接口；阈值触发 `maybe_summarize_history()`。
   - 在 `context.py` 实现 `parse_query_slots(user_query)` 与 `merge_with_memory()`。
3. **映射优化**：
   - 在 `mapping.py` 读取映射（主/备），`SYNONYMS` 与 `get_relevant_columns(user_query, context, k=40)`；生成精简 `columns_desc`。
4. **Prompt 与超限**：
   - 在 `llm.py` 用 Top‑K 列与上下文摘要构建 `schema_info`；实现 token 预算估算与 `k` 动态降级；生成 SQL 与滚动摘要。
5. **数据库与重命名**：
   - 在 `db.py` 执行查询并按映射重命名（只对存在的列）。
6. **UI 集成**：
   - 在 `ui.py` 构建 Sidebar 的上下文卡片（站点/设备/时间范围）与主区“已应用上下文”提示；在 `app.py` 组装全流程。
7. **回退与健壮性**：
   - 当映射为空/无匹配时，降级到内置关键列集（包含 `ts` 与 `dc` 等常用列）；错误时保持旧逻辑可回退。

## 超限策略细化
- 历史消息窗口：保留最近 6~8 条 + 滚动摘要；摘要写入 `config.memory.summary`。
- Schema 精简：Top‑K 动态 40→25→15；确保包含当前查询核心列与 `ts`。
- 当仍超限：提示用户并自动进一步压缩摘要（仅保留意图/槽位）。

## 验证要点
- 多轮对话自动继承上下文；Sidebar 修改即时生效。
- 生成 SQL 使用正确列（如“有功功率”→`dc`），Prompt 长度稳定。
- 超限时自动摘要与精简，无报错；查询与图表正常。

## 交付
- 重构代码至 `plus/` 文件夹并完成集成；更新启动方式为 `streamlit run plus/app.py`；不新增文档文件。确认后立即实施并验证。