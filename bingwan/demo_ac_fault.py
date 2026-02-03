import pandas as pd
import numpy as np
import taosws
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score, roc_auc_score, roc_curve, classification_report
import matplotlib.pyplot as plt
import os
from loguru import logger

# 配置
TDENGINE_URL = "taosws://root:taosdata@192.168.2.110:6041"
DB_NAME = "station_data"
TABLE_NAME = "stable_gtjjlfgdzf"
OUTPUT_DIR = "bingwan"

# 特征映射 (基于 column_mapping.json)
# AC 侧故障检测主要关注电压、电流、频率、功率
FEATURES = {
    'ct': 'Grid_Voltage_L1',
    'cu': 'Grid_Voltage_L2',
    'cv': 'Grid_Voltage_L3',
    'cw': 'Grid_Frequency',
    'cx': 'Grid_Current_L1',
    'cy': 'Grid_Current_L2',
    'cz': 'Grid_Current_L3',
    'dc': 'Active_Power',
    'da': 'Reactive_Power'
}

def load_data(limit=50000):
    """从 TDengine 加载数据"""
    logger.info(f"Connecting to TDengine: {TDENGINE_URL}")
    try:
        conn = taosws.connect(TDENGINE_URL)
        cursor = conn.cursor()

        cols = ",".join(FEATURES.keys())
        sql = f"SELECT ts, {cols} FROM {DB_NAME}.{TABLE_NAME} LIMIT {limit}"
        logger.info(f"Executing SQL: {sql}")

        cursor.execute(sql)
        data = cursor.fetchall()

        # 获取列名 (如果 cursor.description 不可用，使用我们请求的列)
        if cursor.description:
            columns = [col[0] for col in cursor.description]
        else:
            columns = ['ts'] + list(FEATURES.keys())

        cursor.close()
        conn.close()

        df = pd.DataFrame(data, columns=columns)

        # 重命名列以便理解
        df.rename(columns=FEATURES, inplace=True)

        # 处理时间戳
        df['ts'] = pd.to_datetime(df['ts'])
        df.set_index('ts', inplace=True)

        # 填充 NaN
        df.fillna(method='ffill', inplace=True)
        df.fillna(0, inplace=True)

        logger.info(f"Loaded {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

def generate_labels(df):
    """
    生成合成故障标签 (Ground Truth)
    论文中使用的是带有故障标记的数据集。由于我们使用的是正常运行数据(假设)，
    我们需要基于规则合成一些故障，或者标记数据中的异常值。

    规则参考并网标准:
    1. 电压异常: 标称值 (假设 690V 或 400V) ±10%
    2. 频率异常: 50Hz ±0.5Hz
    """
    # 自动推断标称电压 (取中位数)
    nominal_voltage = df['Grid_Voltage_L1'].median()
    nominal_freq = df['Grid_Frequency'].median()

    logger.info(f"Inferred Nominal Voltage: {nominal_voltage:.2f}V")
    logger.info(f"Inferred Nominal Frequency: {nominal_freq:.2f}Hz")

    # 如果数据全是 0 (例如传感器未连接)，则无法进行
    if nominal_voltage < 10:
        logger.warning("Voltage seems too low, maybe data is invalid. Using default 690V.")
        nominal_voltage = 690
    if nominal_freq < 40:
        nominal_freq = 50

    # 定义故障规则
    # 正常范围: [0.9*Vn, 1.1*Vn]
    v_min, v_max = 0.9 * nominal_voltage, 1.1 * nominal_voltage
    f_min, f_max = nominal_freq - 0.5, nominal_freq + 0.5

    labels = np.zeros(len(df))

    # 电压故障 (任意一相)
    v_fault = (
        (df['Grid_Voltage_L1'] < v_min) | (df['Grid_Voltage_L1'] > v_max) |
        (df['Grid_Voltage_L2'] < v_min) | (df['Grid_Voltage_L2'] > v_max) |
        (df['Grid_Voltage_L3'] < v_min) | (df['Grid_Voltage_L3'] > v_max)
    )

    # 频率故障
    f_fault = (df['Grid_Frequency'] < f_min) | (df['Grid_Frequency'] > f_max)

    labels[v_fault | f_fault] = 1

    # 为了演示模型能力，如果故障太少，我们人工注入一些故障
    n_faults = np.sum(labels)
    if n_faults < len(df) * 0.1: # 如果故障少于 10%
        logger.info("Natural faults are rare, injecting synthetic faults...")
        n_inject = int(len(df) * 0.1)
        indices = np.random.choice(len(df), n_inject, replace=False)

        # 注入电压暂降 (0.5 pu)
        df.iloc[indices, df.columns.get_loc('Grid_Voltage_L1')] *= 0.5
        labels[indices] = 1

    df['Label'] = labels
    logger.info(f"Fault Ratio: {np.mean(labels):.2%}")
    return df

def train_and_evaluate(df):
    """训练 KNN, LR, ANN 并对比"""
    X = df.drop(columns=['Label'])
    y = df['Label']

    # 标准化
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.3, random_state=42)

    models = {
        'KNN': KNeighborsClassifier(n_neighbors=5),
        'Logistic Regression': LogisticRegression(max_iter=1000),
        'ANN (MLP)': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
    }

    results = {}
    plt.figure(figsize=(10, 6))

    for name, model in models.items():
        logger.info(f"Training {name}...")
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_prob)

        results[name] = {'Accuracy': acc, 'AUC': auc}
        logger.info(f"{name} - Accuracy: {acc:.4f}, AUC: {auc:.4f}")

        # ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        plt.plot(fpr, tpr, label=f'{name} (AUC = {auc:.2f})')

    plt.plot([0, 1], [0, 1], 'k--', label='Random Chance')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curves Comparison (AC Fault Detection)')
    plt.legend(loc='lower right')
    plt.grid(True)

    plot_path = os.path.join(OUTPUT_DIR, 'roc_comparison.png')
    plt.savefig(plot_path)
    logger.info(f"Saved ROC plot to {plot_path}")

    return results

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. 加载数据
    df = load_data()

    # 2. 生成标签 (模拟论文场景)
    df = generate_labels(df)

    # 3. 训练与评估
    results = train_and_evaluate(df)

    # 4. 输出总结
    print("\n" + "="*40)
    print("Paper Implementation Results Summary")
    print("="*40)
    for name, metrics in results.items():
        print(f"{name:20s} | Accuracy: {metrics['Accuracy']:.4f} | AUC: {metrics['AUC']:.4f}")
    print("="*40)

if __name__ == "__main__":
    main()
