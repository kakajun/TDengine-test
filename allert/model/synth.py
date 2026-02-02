import numpy as np
import pandas as pd
from loguru import logger

class DataSynthesizer:
    def __init__(self, base_df):
        # 仅从数值列计算统计信息
        self.numeric_df = base_df.select_dtypes(include=[np.number])
        self.stats = self.numeric_df.describe().transpose()
        self.columns = self.numeric_df.columns

    def generate(self, n_samples=1000, anomaly_ratio=0.1):
        logger.info(f"Synthesizing {n_samples} samples with {anomaly_ratio} anomaly ratio...")
        data = {}
        labels = np.zeros(n_samples, dtype=int)

        n_anomalies = int(n_samples * anomaly_ratio)
        # 前 n_anomalies 个样本为正样本 (1)
        labels[:n_anomalies] = 1

        for col in self.columns:
            mean = self.stats.loc[col, 'mean']
            std = self.stats.loc[col, 'std']

            # 处理常数或 NaN
            if pd.isna(std) or std == 0:
                std = 1.0 if mean == 0 else abs(mean * 0.1)
            if pd.isna(mean):
                mean = 0

            # 生成基础数据 (正态分布)
            vals = np.random.normal(loc=mean, scale=std, size=n_samples)

            # 注入异常
            # 在这个简单的合成器中，我们将异常行的均值偏移 3 个标准差
            # 我们将此偏移应用于列的随机子集以模拟多变量故障
            # 但在这里，为了简单起见，我们将其应用于所有列，或者每列有 50% 的随机概率
            if np.random.random() > 0.5:
                # 偏移方向：随机向上或向下
                direction = 1 if np.random.random() > 0.5 else -1
                vals[:n_anomalies] += (direction * 3 * std)

            data[col] = vals

        df = pd.DataFrame(data)
        return df, labels
