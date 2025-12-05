import numpy as np
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import logging

from .feature_engineer import FeatureEngineer
from ..core.config import ML_CONFIG, FEATURE_CONFIG, MODELS_DIR

logger = logging.getLogger(__name__)


class MLClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(**ML_CONFIG['random_forest'])
        self.feature_engineer = FeatureEngineer()
        self.trained = False
        self.model_path = MODELS_DIR / 'rf_classifier.pkl'
        self.feat_eng_path = MODELS_DIR / 'feature_engineer.pkl'
        self.load_model()

    def generate_synthetic_data(self, n_samples=None):
        if n_samples is None:
            n_samples = ML_CONFIG['synthetic_samples']

        logger.info(f"Generating {n_samples} synthetic training samples")
        np.random.seed(42)
        data = []
        labels = []

        for i in range(n_samples):
            size_mb = np.random.lognormal(0, 2)
            created_days = np.random.uniform(150, 1500)

            if np.random.random() < 0.70:
                accessed_days = np.random.uniform(200, created_days)
            else:
                accessed_days = np.random.uniform(0, 150)

            modified_days = np.random.uniform(accessed_days, created_days)
            is_disposable = np.random.choice([True, False], p=[0.45, 0.55])
            is_hidden = np.random.choice([True, False], p=[0.10, 0.90])
            depth = int(np.random.exponential(3) + 2)

            label = 1
            del_score = 0
            keep_score = 0

            if accessed_days < 60:
                keep_score += 2
            if accessed_days < 180:
                keep_score += 1

            if is_disposable:
                del_score += 2
            if accessed_days > 270:
                del_score += 3
            if accessed_days > 540:
                del_score += 2
            if size_mb > 150 and accessed_days > 180:
                del_score += 2
            if size_mb > 50 and accessed_days > 365:
                del_score += 1
            if modified_days > 540:
                del_score += 1
            if is_hidden and accessed_days > 270:
                del_score += 1

            net = del_score - keep_score
            if net >= 2:
                label = 0
            else:
                label = 1

            file_meta = {
                'size_mb': size_mb,
                'size_bytes': size_mb * 1024 * 1024,
                'size_kb': size_mb * 1024,
                'created_days_ago': created_days,
                'modified_days_ago': modified_days,
                'accessed_days_ago': accessed_days,
                'is_hidden': is_hidden,
                'depth': depth,
                'is_disposable_ext': is_disposable,
                'in_system_folder': False,
                'days_since_modification': modified_days,
                'days_since_access': accessed_days,
                'access_to_modify_ratio': accessed_days / max(modified_days, 0.1),
                'is_recent': accessed_days < 7,
                'is_old': modified_days > 365,
                'is_large': size_mb > 100,
                'extension': 'tmp' if is_disposable else np.random.choice(['pdf', 'docx', 'jpg', 'mp4', 'mp3', 'zip', 'avi']),
                'category': 'disposable' if is_disposable else np.random.choice(['documents', 'images', 'videos', 'audio', 'archives']),
            }

            data.append(file_meta)
            labels.append(label)

        labels = np.array(labels)
        del_cnt = np.sum(labels == 0)
        keep_cnt = np.sum(labels == 1)

        curr_del_ratio = del_cnt / len(labels)
        target_del = 0.50

        logger.info(f"Initial: {keep_cnt} KEEP ({keep_cnt/len(labels)*100:.1f}%), "
                   f"{del_cnt} DELETE ({del_cnt/len(labels)*100:.1f}%)")

        if curr_del_ratio < target_del - 0.05:
            n_extra = int((target_del * len(labels)) - del_cnt)

            for i in range(n_extra):
                size_mb = np.random.lognormal(1, 2)
                accessed_days = np.random.uniform(200, 1500)
                modified_days = accessed_days + np.random.uniform(0, 200)
                created_days = modified_days + np.random.uniform(0, 200)

                file_meta = {
                    'size_mb': size_mb,
                    'size_bytes': size_mb * 1024 * 1024,
                    'size_kb': size_mb * 1024,
                    'created_days_ago': created_days,
                    'modified_days_ago': modified_days,
                    'accessed_days_ago': accessed_days,
                    'is_hidden': False,
                    'depth': int(np.random.exponential(3) + 2),
                    'is_disposable_ext': True,
                    'in_system_folder': False,
                    'days_since_modification': modified_days,
                    'days_since_access': accessed_days,
                    'access_to_modify_ratio': accessed_days / max(modified_days, 0.1),
                    'is_recent': False,
                    'is_old': True,
                    'is_large': True,
                    'extension': np.random.choice(['tmp', 'cache', 'bak', 'log', 'old']),
                    'category': 'disposable',
                }

                data.append(file_meta)
                labels = np.append(labels, 0)

        elif curr_del_ratio > target_del + 0.05:
            n_extra = int(keep_cnt - (len(labels) - target_del * len(labels)))

            for i in range(n_extra):
                size_mb = np.random.lognormal(0, 1.5)
                accessed_days = np.random.uniform(0, 120)
                modified_days = accessed_days + np.random.uniform(0, 100)
                created_days = modified_days + np.random.uniform(0, 200)

                file_meta = {
                    'size_mb': size_mb,
                    'size_bytes': size_mb * 1024 * 1024,
                    'size_kb': size_mb * 1024,
                    'created_days_ago': created_days,
                    'modified_days_ago': modified_days,
                    'accessed_days_ago': accessed_days,
                    'is_hidden': False,
                    'depth': int(np.random.exponential(2) + 2),
                    'is_disposable_ext': False,
                    'in_system_folder': False,
                    'days_since_modification': modified_days,
                    'days_since_access': accessed_days,
                    'access_to_modify_ratio': accessed_days / max(modified_days, 0.1),
                    'is_recent': True,
                    'is_old': False,
                    'is_large': False,
                    'extension': np.random.choice(['pdf', 'docx', 'jpg', 'png', 'mp4', 'mp3']),
                    'category': np.random.choice(['documents', 'images', 'videos', 'audio']),
                }

                data.append(file_meta)
                labels = np.append(labels, 1)

        final_del = np.sum(labels == 0)
        final_keep = np.sum(labels == 1)

        logger.info(f"Final: {final_keep} KEEP ({final_keep/len(labels)*100:.1f}%), "
                   f"{final_del} DELETE ({final_del/len(labels)*100:.1f}%)")

        return data, labels

    def train(self, file_data=None, labels=None):
        logger.info("Training ML classifier...")

        if file_data is None or labels is None:
            file_data, labels = self.generate_synthetic_data()

        features = self.feature_engineer.prepare_features(file_data, fit=True)
        X_scaled = self.feature_engineer.scale_features(features, fit=True)

        self.model.fit(X_scaled, labels)
        self.trained = True

        acc = self.model.score(X_scaled, labels)
        logger.info(f"Training complete. Accuracy: {acc:.2%}")

        if hasattr(self.model, 'feature_importances_'):
            feat_names = self.feature_engineer.get_feature_importance_names()
            importances = self.model.feature_importances_

            top_idx = np.argsort(importances)[-10:][::-1]
            logger.info("Top 10 important features:")
            for idx in top_idx:
                if idx < len(feat_names):
                    logger.info(f"  {feat_names[idx]}: {importances[idx]:.4f}")

        self.save_model()

    def predict(self, file_data):
        if not self.trained:
            logger.warning("Model not trained, training now")
            self.train()

        if not file_data:
            return np.array([]), np.array([])

        features = self.feature_engineer.prepare_features(file_data, fit=False)
        X_scaled = self.feature_engineer.scale_features(features, fit=False)

        preds = self.model.predict(X_scaled)
        probs = self.model.predict_proba(X_scaled)

        logger.debug(f"Predicted {len(preds)} files: {sum(preds)} KEEP, {len(preds) - sum(preds)} DELETE")

        return preds, probs

    def predict_single(self, file_meta):
        preds, probs = self.predict([file_meta])

        if len(preds) > 0:
            pred = int(preds[0])
            conf = float(probs[0][pred])
            return pred, conf

        return 1, 0.5

    def save_model(self):
        if not self.trained:
            logger.warning("Cannot save untrained model")
            return

        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.feat_eng_path, 'wb') as f:
                pickle.dump(self.feature_engineer, f)
            logger.info(f"Model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")

    def load_model(self):
        if not self.model_path.exists() or not self.feat_eng_path.exists():
            logger.debug("No saved model found")
            return False

        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.feat_eng_path, 'rb') as f:
                self.feature_engineer = pickle.load(f)

            self.trained = True
            logger.info(f"Model loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def evaluate(self, test_data, test_labels):
        preds, probs = self.predict(test_data)

        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

        metrics = {
            'accuracy': accuracy_score(test_labels, preds),
            'precision': precision_score(test_labels, preds, zero_division=0),
            'recall': recall_score(test_labels, preds, zero_division=0),
            'f1_score': f1_score(test_labels, preds, zero_division=0),
        }

        logger.info(f"Evaluation metrics: {metrics}")
        return metrics
