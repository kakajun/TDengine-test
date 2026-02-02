import pandas as pd
from loguru import logger

class Rule:
    def __init__(self, config):
        self.name = config.get('name')
        self.expr = config.get('expr')
        self.severity = config.get('severity', 'info')
        self.window = config.get('window') # 例如 "5m any"
        self.dedup = config.get('dedup') # 例如 "10m"
        self.message = config.get('message', self.name)

    def evaluate(self, df):
        try:
            # 使用 pandas eval。如果安装了 numexpr，它支持 numexpr 后端。
            # engine='numexpr' 更快但类型检查更严格。
            # engine='python' 更安全。
            # 这里我们使用默认设置 (自动选择)。
            result_series = df.eval(self.expr)
        except Exception as e:
            logger.error(f"Error evaluating rule '{self.name}' with expr '{self.expr}': {e}")
            return pd.Series(False, index=df.index)

        # 窗口逻辑
        if self.window:
            try:
                parts = self.window.split()
                duration = parts[0]
                func = parts[1] if len(parts) > 1 else 'any'

                # 滑动窗口
                # 如果需要，将布尔值转换为整数进行计算，但 rolling 大多时候可以将布尔值作为浮点数处理
                # Rolling max 等同于 'any'，min 等同于 'all'
                r = result_series.astype(int).rolling(window=duration)

                if func == 'any':
                    result_series = r.max() > 0
                elif func == 'all':
                    result_series = r.min() > 0
                elif func == 'sum':
                     # 例如 count > 5
                     pass
            except Exception as e:
                logger.error(f"Error applying window '{self.window}' for rule '{self.name}': {e}")

        return result_series.fillna(False).astype(bool)

class RuleEngine:
    def __init__(self, rules_config):
        self.rules = [Rule(r) for r in rules_config]

    def run(self, df):
        all_alerts = []

        for rule in self.rules:
            # 1. 评估规则
            triggered_series = rule.evaluate(df)

            if not triggered_series.any():
                continue

            # 2. 提取时间戳
            triggered_indices = triggered_series[triggered_series].index

            # 3. 去重 (离线/批处理模式)
            # 如果设置了去重，我们遍历并跳过在前一个告警窗口内的告警
            if rule.dedup:
                kept_indices = []
                last_ts = None
                dedup_delta = pd.to_timedelta(rule.dedup)

                for ts in triggered_indices:
                    if last_ts is None or (ts - last_ts) > dedup_delta:
                        kept_indices.append(ts)
                        last_ts = ts

                final_indices = kept_indices
            else:
                final_indices = triggered_indices

            # 4. 创建告警对象
            for ts in final_indices:
                row = df.loc[ts]
                # row 可能是 Series (单行) 或 DataFrame (重复索引)
                # 为简单起见，假设索引唯一或取第一条
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]

                alert = {
                    'timestamp': ts,
                    'device_id': row.get('device_id', 'unknown'),
                    'rule_name': rule.name,
                    'severity': rule.severity,
                    'message': rule.message,
                    # 可选: 捕获相关数值？
                    # 自动从表达式解析比较复杂，但很有价值。
                }
                all_alerts.append(alert)

        return pd.DataFrame(all_alerts)
