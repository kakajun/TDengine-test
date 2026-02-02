from allert.model.synth import DataSynthesizer
from allert.model.sklearn_model import GenericModel
from allert.rule_engine import RuleEngine
from allert.data_loader import DataLoader
from allert.mapping_loader import MappingLoader
import click
import yaml
from loguru import logger
import os
import sys

# 如果直接运行，确保 src 在路径中
sys.path.append(os.getcwd())


@click.group()
def cli():
    pass


def load_yaml(path):
    if not os.path.exists(path):
        logger.error(f"Config file not found: {path}")
        sys.exit(1)
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@cli.command()
@click.option('--config', default='configs/config.yaml', help='Path to config file')
@click.option('--input', default=None, help='Input CSV file')
@click.option('--sql', default=None, help='SQL query for TSDB')
@click.option('--output', default=None, help='Output CSV file')
def run(config, input, sql, output):
    """Run rule engine on input CSV or TSDB"""
    cfg = load_yaml(config)

    # 初始化组件
    mapping_loader = MappingLoader(
        cfg['data']['mapping_path'],
        encoding=cfg['data'].get('mapping_encoding', 'utf-8')
    )
    data_loader = DataLoader(mapping_loader)

    # 加载规则
    rules_path = cfg['rules']['path']
    if not os.path.exists(rules_path):
        # 回退到相对于配置文件的路径
        rules_path = os.path.join(os.path.dirname(
            config), os.path.basename(rules_path))

    rules_config = load_yaml(rules_path)
    engine = RuleEngine(rules_config)

    # 加载数据
    try:
        if input:
            df = data_loader.load_csv(input)
        else:
            # 默认使用 SQL
            query = sql if sql else "SELECT * FROM station_data.stable_gtjjlfgdzf LIMIT 1000"
            df = data_loader.load_from_tsdb(query)

        logger.info(f"Loaded data shape: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # 运行规则
    logger.info("Running rule engine...")
    alerts = engine.run(df)

    if not alerts.empty:
        logger.warning(f"Generated {len(alerts)} alerts.")
        # 输出
        out_path = output if output else cfg['output']['path']
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        alerts.to_csv(out_path, index=False)
        logger.info(f"Alerts saved to {out_path}")

        # 打印预览
        print(alerts[['timestamp', 'rule_name', 'message']].head())
    else:
        logger.info("No alerts generated.")


@cli.command()
@click.option('--config', default='configs/config.yaml')
@click.option('--input', default=None, help='Input CSV for training base')
@click.option('--sql', default=None, help='SQL query for TSDB')
def train_model(config, input, sql):
    """Train a model (Demo)"""
    cfg = load_yaml(config)

    # 加载数据
    mapping_loader = MappingLoader(
        cfg['data']['mapping_path'],
        encoding=cfg['data'].get('mapping_encoding', 'utf-8')
    )
    data_loader = DataLoader(mapping_loader)

    try:
        if input:
            df = data_loader.load_csv(input)
        else:
            # 默认使用 SQL
            query = sql if sql else "SELECT * FROM station_data.stable_gtjjlfgdzf LIMIT 1000"
            df = data_loader.load_from_tsdb(query)

        logger.info(f"Loaded base data shape: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return

    # 合成数据
    synth = DataSynthesizer(df)
    X_train, y_train = synth.generate(n_samples=2000, anomaly_ratio=0.1)

    # 训练
    model_path = cfg.get('model', {}).get('model_path', 'out/model.pkl')
    logger.info(f"Training LightGBM/RF model...")

    model = GenericModel(algorithm='lgbm')  # 或 'rf'
    model.train(X_train, y_train)

    model.save(model_path)
    logger.info(f"Model saved to {model_path}")


if __name__ == '__main__':
    cli()
