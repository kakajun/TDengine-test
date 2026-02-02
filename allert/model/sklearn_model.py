from .base import BaseModel
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
try:
    import lightgbm as lgb
    HAS_LGBM = True
except ImportError:
    HAS_LGBM = False
import os
from loguru import logger

class GenericModel(BaseModel):
    def __init__(self, algorithm='rf', **kwargs):
        self.algorithm = algorithm
        if algorithm == 'rf':
            self.model = RandomForestClassifier(**kwargs)
        elif algorithm == 'lgbm':
            if HAS_LGBM:
                self.model = lgb.LGBMClassifier(**kwargs)
            else:
                logger.warning("LightGBM not installed, falling back to RandomForest")
                self.model = RandomForestClassifier(**kwargs)
        else:
            self.model = LogisticRegression(**kwargs)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        return None

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Model saved to {path}")

    def load(self, path):
        self.model = joblib.load(path)
        logger.info(f"Model loaded from {path}")
