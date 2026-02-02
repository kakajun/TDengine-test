import pandas as pd
from loguru import logger
from .mapping_loader import MappingLoader
import os

class DataLoader:
    def __init__(self, mapping_loader: MappingLoader):
        self.mapping_loader = mapping_loader

    def load_from_tsdb(self, sql="SELECT * FROM station_data.stable_gtjjlfgdzf LIMIT 1000"):
        import taosws
        logger.info(f"Loading data from TDengine with SQL: {sql}")
        try:
            conn = taosws.connect("taosws://root:taosdata@localhost:6041")
            cursor = conn.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
            fields = [field[0] for field in cursor.description]
            cursor.close()
            conn.close()

            df = pd.DataFrame(data, columns=fields)
            
            # 标准化列名
            if 'ts' in df.columns:
                df['timestamp'] = pd.to_datetime(df['ts'])
                # 保留原始 ts 列可能有用，或者直接 drop
                df.drop(columns=['ts'], inplace=True)
            
            if 'equ_code' in df.columns:
                df['device_id'] = df['equ_code']
                # drop 原始列
                df.drop(columns=['equ_code'], inplace=True)
                
            # 应用字段映射
            df = self.mapping_loader.apply_mapping(df)

            # 设置索引
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to load from TSDB: {e}")
            raise e

    def load_csv(self, file_path):
        logger.info(f"Loading data from {file_path}")
        try:
            df = pd.read_csv(file_path)
        except UnicodeDecodeError:
            logger.warning("UTF-8 decode failed, retrying with GBK")
            df = pd.read_csv(file_path, encoding='gbk')

        # 1. 解析主键 (PK)
        if 'PK' in df.columns:
            # PK 格式: 设备ID|YYYY-MM-DDHH:MM:SS
            # 按第一个 '|' 分割
            split_pk = df['PK'].str.split('|', n=1, expand=True)
            if split_pk.shape[1] == 2:
                df['device_id'] = split_pk[0]
                raw_time = split_pk[1]

                # 基于用户示例，格式似乎是 %Y-%m-%d%H:%M:%S
                # 例如 "2025-12-1514:47:10"
                df['timestamp'] = pd.to_datetime(raw_time, format='%Y-%m-%d%H:%M:%S', errors='coerce')

                # 如果格式解析失败 (NaT)，尝试标准格式
                mask_nat = df['timestamp'].isna()
                if mask_nat.any():
                    df.loc[mask_nat, 'timestamp'] = pd.to_datetime(raw_time[mask_nat], errors='coerce')

            df.drop(columns=['PK'], inplace=True)

        # 2. 展开位域 (bit) 列
        if 'bit' in df.columns:
            # 检查 bit 列是否为对象/字符串类型
            if df['bit'].dtype == 'O':
                # 分割并展开
                bit_df = df['bit'].str.split('|', expand=True)
                # 重命名列
                bit_df.columns = [f'bit_{i}' for i in range(bit_df.shape[1])]
                # 转换为数值类型
                bit_df = bit_df.apply(pd.to_numeric, errors='coerce').fillna(0)

                df = pd.concat([df, bit_df], axis=1)
                df.drop(columns=['bit'], inplace=True)

        # 3. 应用字段映射
        df = self.mapping_loader.apply_mapping(df)

        # 设置索引
        if 'timestamp' in df.columns:
            # 删除时间戳无效的行
            df = df.dropna(subset=['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
        else:
            logger.warning("No timestamp column found/parsed.")

        return df
