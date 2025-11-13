"""
Anomaly detection for identifying unusual files
"""

import numpy as np
import pickle
from typing import List, Dict
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

from ..core.config import ML_CONFIG, MODELS_DIR

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalous files using Isolation Forest"""
    
    def __init__(self):
        self.model = IsolationForest(**ML_CONFIG['isolation_forest'])
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.model_path = MODELS_DIR / 'anomaly_detector.pkl'
        self.scaler_path = MODELS_DIR / 'anomaly_scaler.pkl'
    
    def prepare_features(self, file_data: List[Dict]) -> np.ndarray:
        """
        Prepare features for anomaly detection
        
        Focuses on characteristics that indicate unusual files:
        - Size (very large or very small)
        - Access patterns (not accessed in long time)
        - Age (very old)
        - Location (unusual depth)
        
        Args:
            file_data: List of file metadata dictionaries
            
        Returns:
            Feature array
        """
        if not file_data:
            return np.array([])
        
        features = []
        for file_meta in file_data:
            feature_vec = [
                file_meta['size_mb'],
                file_meta['accessed_days_ago'],
                file_meta['modified_days_ago'],
                file_meta['depth'],
                file_meta.get('dormant_period', 
                             file_meta['accessed_days_ago'] - file_meta['modified_days_ago']),
                np.log1p(file_meta['size_mb']),  # Log-scaled size
            ]
            features.append(feature_vec)
        
        return np.array(features)
    
    def fit(self, file_data: List[Dict]):
        """
        Fit the anomaly detector
        
        Args:
            file_data: List of file metadata for fitting
        """
        logger.info("Fitting anomaly detector...")
        
        features = self.prepare_features(file_data)
        
        if len(features) == 0:
            logger.warning("No features to fit")
            return
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Fit model
        self.model.fit(features_scaled)
        self.is_fitted = True
        
        logger.info(f"Anomaly detector fitted on {len(features)} samples")
        
        # Save model
        self.save_model()
    
    def detect(self, file_data: List[Dict]) -> np.ndarray:
        """
        Detect anomalies in file data
        
        Args:
            file_data: List of file metadata dictionaries
            
        Returns:
            Binary array: 1 = anomaly, 0 = normal
        """
        if not file_data:
            return np.array([])
        
        features = self.prepare_features(file_data)
        
        if len(features) == 0:
            return np.array([])
        
        # Fit if not already fitted
        if not self.is_fitted:
            logger.warning("Detector not fitted, fitting now")
            self.fit(file_data)
        
        # Scale features
        features_scaled = self.scaler.transform(features)
        
        # Predict (-1 = anomaly, 1 = normal)
        predictions = self.model.predict(features_scaled)
        
        # Convert to binary (1 = anomaly, 0 = normal)
        anomalies = (predictions == -1).astype(int)
        
        anomaly_count = np.sum(anomalies)
        logger.debug(f"Detected {anomaly_count} anomalies out of {len(file_data)} files "
                    f"({anomaly_count/len(file_data)*100:.1f}%)")
        
        return anomalies
    
    def get_anomaly_scores(self, file_data: List[Dict]) -> np.ndarray:
        """
        Get anomaly scores for files
        
        Args:
            file_data: List of file metadata dictionaries
            
        Returns:
            Array of anomaly scores (more negative = more anomalous)
        """
        if not file_data:
            return np.array([])
        
        features = self.prepare_features(file_data)
        
        if len(features) == 0:
            return np.array([])
        
        if not self.is_fitted:
            self.fit(file_data)
        
        features_scaled = self.scaler.transform(features)
        scores = self.model.score_samples(features_scaled)
        
        return scores
    
    def detect_with_reasons(self, file_data: List[Dict]) -> List[Dict]:
        """
        Detect anomalies and provide reasons
        
        Args:
            file_data: List of file metadata dictionaries
            
        Returns:
            List of dictionaries with anomaly info and reasons
        """
        anomalies = self.detect(file_data)
        scores = self.get_anomaly_scores(file_data)
        
        results = []
        for i, (file_meta, is_anomaly, score) in enumerate(zip(file_data, anomalies, scores)):
            reasons = []
            
            if is_anomaly:
                # Determine why it's anomalous
                if file_meta['size_mb'] > 1000:
                    reasons.append(f"Very large file ({file_meta['size_mb']:.1f} MB)")
                
                if file_meta['accessed_days_ago'] > 365:
                    reasons.append(f"Not accessed in {file_meta['accessed_days_ago']:.0f} days")
                
                if file_meta['modified_days_ago'] > 730:
                    reasons.append(f"Very old (modified {file_meta['modified_days_ago']:.0f} days ago)")
                
                if file_meta['depth'] > 15:
                    reasons.append(f"Deeply nested (depth {file_meta['depth']})")
                
                dormant = file_meta['accessed_days_ago'] - file_meta['modified_days_ago']
                if dormant > 180:
                    reasons.append(f"Dormant for {dormant:.0f} days")
            
            results.append({
                'is_anomaly': bool(is_anomaly),
                'anomaly_score': float(score),
                'reasons': reasons
            })
        
        return results
    
    def save_model(self):
        """Save the fitted model"""
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
    
    def load_model(self) -> bool:
        """
        Load a saved model
        
        Returns:
            True if successful, False otherwise
        """
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