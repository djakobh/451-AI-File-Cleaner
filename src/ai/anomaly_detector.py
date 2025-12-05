import numpy as np
import pickle
from typing import List, Dict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

from ..core.config import ML_CONFIG, MODELS_DIR

logger = logging.getLogger(__name__)


class AnomalyDetector:
    def __init__(self):
        if_config = {k: v for k, v in ML_CONFIG['isolation_forest'].items()
                     if k not in ['use_threshold_based_detection']}
        self.model = IsolationForest(**if_config)
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.model_path = MODELS_DIR / 'anomaly_detector.pkl'
        self.scaler_path = MODELS_DIR / 'anomaly_scaler.pkl'
        self.use_threshold_based = ML_CONFIG['isolation_forest'].get('use_threshold_based_detection', True)

    def prepare_features(self, file_data):
        if not file_data:
            return np.array([])

        features = []
        for f in file_data:
            feat = [
                f['size_mb'],
                f['accessed_days_ago'],
                f['modified_days_ago'],
                f['depth'],
                f.get('dormant_period', f['accessed_days_ago'] - f['modified_days_ago']),
                np.log1p(f['size_mb']),
            ]
            features.append(feat)

        return np.array(features)

    def fit(self, file_data):
        logger.info("Fitting anomaly detector...")

        features = self.prepare_features(file_data)
        if len(features) == 0:
            logger.warning("No features to fit")
            return

        features_scaled = self.scaler.fit_transform(features)
        self.model.fit(features_scaled)
        self.is_fitted = True

        logger.info(f"Anomaly detector fitted on {len(features)} samples")
        self.save_model()

    def detect(self, file_data):
        if not file_data:
            return np.array([])

        if self.use_threshold_based:
            anomalies = []
            for f in file_data:
                anom = False

                if f['size_mb'] > 76800:
                    anom = True
                elif f['accessed_days_ago'] > 1277:
                    anom = True
                elif f['modified_days_ago'] > 1642:
                    anom = True
                elif f['depth'] > 22:
                    anom = True
                else:
                    dorm = f['accessed_days_ago'] - f['modified_days_ago']
                    if dorm > 912:
                        anom = True

                anomalies.append(1 if anom else 0)

            anomalies = np.array(anomalies)
            cnt = np.sum(anomalies)
            logger.debug(f"Detected {cnt} anomalies out of {len(file_data)} files "
                        f"({cnt/len(file_data)*100:.1f}%)")
            return anomalies
        else:
            features = self.prepare_features(file_data)
            if len(features) == 0:
                return np.array([])

            if not self.is_fitted:
                logger.warning("Detector not fitted, fitting now")
                self.fit(file_data)

            features_scaled = self.scaler.transform(features)
            predictions = self.model.predict(features_scaled)
            anomalies = (predictions == -1).astype(int)

            cnt = np.sum(anomalies)
            logger.debug(f"Detected {cnt} anomalies out of {len(file_data)} files ({cnt/len(file_data)*100:.1f}%)")
            return anomalies

    def get_anomaly_scores(self, file_data):
        if not file_data:
            return np.array([])

        features = self.prepare_features(file_data)
        if len(features) == 0:
            return np.array([])

        if not self.is_fitted:
            self.fit(file_data)

        features_scaled = self.scaler.transform(features)
        return self.model.score_samples(features_scaled)

    def detect_with_reasons(self, file_data):
        anomalies = self.detect(file_data)
        scores = self.get_anomaly_scores(file_data)

        results = []
        for i, (f, is_anom, score) in enumerate(zip(file_data, anomalies, scores)):
            reasons = []

            if is_anom:
                if f['size_mb'] > 76800:
                    reasons.append(f"Very large file ({f['size_mb']:.1f} MB)")
                if f['accessed_days_ago'] > 1277:
                    reasons.append(f"Not accessed in {f['accessed_days_ago']:.0f} days")
                if f['modified_days_ago'] > 1642:
                    reasons.append(f"Very old (modified {f['modified_days_ago']:.0f} days ago)")
                if f['depth'] > 22:
                    reasons.append(f"Deeply nested (depth {f['depth']})")

                dorm = f['accessed_days_ago'] - f['modified_days_ago']
                if dorm > 912:
                    reasons.append(f"Dormant for {dorm:.0f} days")

            results.append({
                'is_anomaly': bool(is_anom),
                'anomaly_score': float(score),
                'reasons': reasons
            })

        return results

    def save_model(self):
        if not self.is_fitted:
            logger.warning("Cannot save unfitted model")
            return

        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            with open(self.scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            logger.info(f"Anomaly detector saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving anomaly detector: {e}")

    def load_model(self):
        if not self.model_path.exists() or not self.scaler_path.exists():
            logger.debug("No saved anomaly detector found")
            return False

        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            self.is_fitted = True
            logger.info(f"Anomaly detector loaded from {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Error loading anomaly detector: {e}")
            return False
