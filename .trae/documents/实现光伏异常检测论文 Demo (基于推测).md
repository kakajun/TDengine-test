我已确认论文 **《AC Fault Detection in On-Grid Photovoltaic Systems by Machine Learning Techniques》** (MDPI Solar 6(1), 6, 2026) 的主要内容。

该论文对比了 **K-Nearest Neighbors (KNN)**、**Logistic Regression (LR)** 和 **Artificial Neural Networks (ANN)** 三种算法在光伏并网系统 AC 侧（逆变器与电网侧）故障检测中的性能。

我计划在 `d:\git\TDengine-test\bingwan\` 目录下实现该论文的 Demo，复现其核心对比逻辑。

### 计划步骤

1.  **创建 Demo 脚本**:
    *   新建 `d:\git\TDengine-test\bingwan\demo_ac_fault.py`。

2.  **数据准备 (Data Preparation)**:
    *   **数据源**: 从 TDengine (`stable_gtjjlfgdzf`) 读取 AC 侧电气参数：`active_power` (有功), `voltage_a/b/c` (三相电压), `current_a/b/c` (三相电流), `frequency` (频率)。
    *   **标签生成 (关键)**: 由于数据库中可能缺乏明确的故障标签，为了演示 **监督学习 (Supervised Learning)** 流程，我将基于并网标准（如电压偏差 >10%、频率偏差 >0.5Hz）生成合成故障标签 (Normal/Fault)，作为模型的 "Ground Truth"。

3.  **模型实现 (Model Implementation)**:
    *   使用 `scikit-learn` 实现论文中的三个核心模型：
        *   **KNN**: `KNeighborsClassifier`
        *   **LR**: `LogisticRegression`
        *   **ANN**: `MLPClassifier` (多层感知机)

4.  **评估与对比 (Evaluation)**:
    *   将数据划分为训练集/测试集 (70%/30%)。
    *   计算并输出各模型的 **准确率 (Accuracy)** 和 **AUC 值**。
    *   生成 ROC 曲线对比图，保存为 `bingwan/roc_comparison.png`。

此方案将完整演示论文中 "使用 ML 技术检测 AC 故障" 的核心思想。