import pandas as pd
from loguru import logger
import chardet
import os

import json

class MappingLoader:
    def __init__(self, mapping_path, encoding='utf-8'):
        self.mapping_path = mapping_path
        self.encoding = encoding
        self.column_map = {}
        if os.path.exists(mapping_path):
            self.load()
        else:
            logger.warning(f"Mapping file not found at {mapping_path}. Using identity mapping.")

    def load(self):
        # 如果是 json 文件
        if self.mapping_path.lower().endswith('.json'):
            try:
                with open(self.mapping_path, 'r', encoding=self.encoding) as f:
                    self.column_map = json.load(f)
                logger.info(f"Loaded {len(self.column_map)} mapping entries from JSON.")
                return
            except Exception as e:
                logger.error(f"Failed to load JSON mapping: {e}")
                return

        # 否则尝试作为 CSV 读取
        try:
            # 尝试使用指定的编码读取
            df = pd.read_csv(self.mapping_path, encoding=self.encoding)
        except (UnicodeDecodeError, pd.errors.ParserError):
            # 回退到自动检测编码
            with open(self.mapping_path, 'rb') as f:
                raw_data = f.read()
                result = chardet.detect(raw_data)
            encoding = result['encoding']
            logger.warning(f"Decoding failed with {self.encoding}, switching to {encoding}")
            df = pd.read_csv(self.mapping_path, encoding=encoding)

        # 清洗并构建映射表
        # 检查列名。用户文件应包含 'index' 和 'chinese_name'
        if 'index' in df.columns and 'chinese_name' in df.columns:
            df['index'] = df['index'].astype(str).str.strip()
            df['chinese_name'] = df['chinese_name'].astype(str).str.strip()
            # 移除空名称
            df = df.dropna(subset=['chinese_name'])
            self.column_map = dict(zip(df['index'], df['chinese_name']))
            logger.info(f"Loaded {len(self.column_map)} mapping entries.")
        else:
            logger.error(f"Mapping file missing required columns 'index' or 'chinese_name'. Found: {df.columns}")

    def get_name(self, index_code):
        return self.column_map.get(index_code, index_code)

    def apply_mapping(self, df_data):
        # 重命名数据 DataFrame 中的列
        # 仅重命名存在于映射表中的列
        rename_dict = {k: v for k, v in self.column_map.items() if k in df_data.columns}

        return df_data.rename(columns=rename_dict)
