"""
Machine Learning classifier for file importance prediction - BALANCED VERSION
"""

import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import logging

from .feature_engineer import FeatureEngineer
from ..core.config import ML_CONFIG, FEATURE_CONFIG, MODELS_DIR

logger = logging.getLogger(__name__)


class MLClassifier:
    """Random Forest classifier for predicting file importance"""
    
    def __init__(self):
        self.model = RandomForestClassifier(**ML_CONFIG['random_forest'])
        self.feature_engineer = FeatureEngineer()
        self.is_trained = False
        self.model_path = MODELS_DIR / 'rf_classifier.pkl'
        self.feature_engineer_path = MODELS_DIR / 'feature_engineer.pkl'
        
        # Try to load existing model
        self.load_model()
    
    def generate_synthetic_data(self, n_samples: int = None) -> Tuple[List[Dict], np.ndarray]:
        """
        Generate synthetic training data - BALANCED for 40-60% deletion
        
        Args:
            n_samples: Number of samples to generate
            
        Returns:
            Tuple of (file_data, labels)
        """
        if n_samples is None:
            n_samples = ML_CONFIG['synthetic_samples']
        
        logger.info(f"Generating {n_samples} synthetic training samples")
        
        np.random.seed(42)
        synthetic_data = []
        labels = []
        
        for i in range(n_samples):
            # Generate realistic file characteristics
            size_mb = np.random.lognormal(0, 2)
            created_days = np.random.uniform(1, 1000)
            accessed_days = np.random.uniform(0, created_days)
            modified_days = np.random.uniform(accessed_days, created_days)
            
            # Random file type (30% disposable is realistic)
            is_disposable = np.random.choice([True, False], p=[0.3, 0.7])
            is_hidden = np.random.choice([True, False], p=[0.08, 0.92])
            
            depth = int(np.random.exponential(3) + 2)
            
            # === BALANCED Labeling for 45-50% deletion ===
            label = 1  # Start with KEEP
            
            delete_score = 0
            keep_score = 0
            
            # KEEP signals (reduced bonuses)
            if accessed_days < 60:  # Used in last 2 months
                keep_score += 2  # Reduced from 3
            
            if accessed_days < 180:  # Used in last 6 months
                keep_score += 1
            
            # DELETE signals (increased penalties)
            if is_disposable:
                delete_score += 2
            
            if accessed_days > 270:  # Not used in 9 months (was 1 year)
                delete_score += 3
            
            if accessed_days > 540:  # Not used in 18 months (was 2 years)
                delete_score += 2  # Extra penalty
            
            if size_mb > 150 and accessed_days > 180:  # Large (150MB+) and 6 months old
                delete_score += 2
            
            if size_mb > 50 and accessed_days > 365:  # Medium (50MB+) and 1 year old
                delete_score += 1
            
            if modified_days > 540:  # Over 18 months old
                delete_score += 1
            
            if is_hidden and accessed_days > 270:  # Hidden and 9 months old
                delete_score += 1
            
            # Lower threshold for more deletions
            net_score = delete_score - keep_score
            if net_score >= 3:  # Lower from 4 to 3
                label = 0  # DELETE
            else:
                label = 1  # KEEP
            
            # Create synthetic file metadata
            file_metadata = {
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
            
            synthetic_data.append(file_metadata)
            labels.append(label)
        
        # Fine-tune the balance to hit 55% KEEP / 45% DELETE
        labels = np.array(labels)
        delete_count = np.sum(labels == 0)
        keep_count = np.sum(labels == 1)
        
        current_delete_ratio = delete_count / len(labels)
        target_delete_ratio = 0.45
        
        logger.info(f"Initial distribution: {keep_count} KEEP ({keep_count/len(labels)*100:.1f}%), "
                   f"{delete_count} DELETE ({delete_count/len(labels)*100:.1f}%)")
        
        # Adjust if needed
        if current_delete_ratio < target_delete_ratio - 0.05:
            # Need more DELETEs - add some old/disposable files
            n_extra_deletes = int((target_delete_ratio * len(labels)) - delete_count)
            
            for i in range(n_extra_deletes):
                # Create clearly deletable files
                size_mb = np.random.lognormal(1, 2)  # Larger files
                accessed_days = np.random.uniform(400, 1500)  # Old
                modified_days = accessed_days + np.random.uniform(0, 200)
                created_days = modified_days + np.random.uniform(0, 200)
                
                file_metadata = {
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
                
                synthetic_data.append(file_metadata)
                labels = np.append(labels, 0)
        
        elif current_delete_ratio > target_delete_ratio + 0.05:
            # Need more KEEPs - add some recent/valuable files
            n_extra_keeps = int(keep_count - (len(labels) - target_delete_ratio * len(labels)))
            
            for i in range(n_extra_keeps):
                # Create clearly keepable files
                size_mb = np.random.lognormal(0, 1.5)
                accessed_days = np.random.uniform(0, 120)  # Recent
                modified_days = accessed_days + np.random.uniform(0, 100)
                created_days = modified_days + np.random.uniform(0, 200)
                
                file_metadata = {
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
                
                synthetic_data.append(file_metadata)
                labels = np.append(labels, 1)
        
        final_delete_count = np.sum(labels == 0)
        final_keep_count = np.sum(labels == 1)
        
        logger.info(f"Final synthetic data: {final_keep_count} KEEP ({final_keep_count/len(labels)*100:.1f}%), "
                   f"{final_delete_count} DELETE ({final_delete_count/len(labels)*100:.1f}%)")
        
        return synthetic_data, labels
    
    def train(self, file_data: Optional[List[Dict]] = None, labels: Optional[np.ndarray] = None):
        """Train the classifier"""
        logger.info("Training ML classifier...")
        
        if file_data is None or labels is None:
            file_data, labels = self.generate_synthetic_data()
        
        features = self.feature_engineer.prepare_features(file_data, fit=True)
        X_scaled = self.feature_engineer.scale_features(features, fit=True)
        
        self.model.fit(X_scaled, labels)
        self.is_trained = True
        
        train_accuracy = self.model.score(X_scaled, labels)
        logger.info(f"Training complete. Accuracy: {train_accuracy:.2%}")
        
        if hasattr(self.model, 'feature_importances_'):
            feature_names = self.feature_engineer.get_feature_importance_names()
            importances = self.model.feature_importances_
            
            top_indices = np.argsort(importances)[-10:][::-1]
            logger.info("Top 10 important features:")
            for idx in top_indices:
                if idx < len(feature_names):
                    logger.info(f"  {feature_names[idx]}: {importances[idx]:.4f}")
        
        self.save_model()
    
    def predict(self, file_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Predict file importance"""
        if not self.is_trained:
            logger.warning("Model not trained, training on synthetic data now")
            self.train()
        
        if not file_data:
            return np.array([]), np.array([])
        
        features = self.feature_engineer.prepare_features(file_data, fit=False)
        X_scaled = self.feature_engineer.scale_features(features, fit=False)
        
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        logger.debug(f"Predicted {len(predictions)} files: "
                    f"{sum(predictions)} KEEP, {len(predictions) - sum(predictions)} DELETE")
        
        return predictions, probabilities
    
    def predict_single(self, file_metadata: Dict) -> Tuple[int, float]:
        """Predict importance for a single file"""
        predictions, probabilities = self.predict([file_metadata])
        
        if len(predictions) > 0:
            pred = int(predictions[0])
            confidence = float(probabilities[0][pred])
            return pred, confidence
        
        return 1, 0.5
    
    def save_model(self):
        """Save trained model and feature engineer"""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        try:
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            with open(self.feature_engineer_path, 'wb') as f:
                pickle.dump(self.feature_engineer, f)
            
            logger.info(f"Model saved to {self.model_path}")
        
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self) -> bool:
        """Load trained model and feature engineer"""
        if not self.model_path.exists() or not self.feature_engineer_path.exists():
            logger.debug("No saved model found")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(self.feature_engineer_path, 'rb') as f:
                self.feature_engineer = pickle.load(f)
            
            self.is_trained = True
            logger.info(f"Model loaded from {self.model_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def evaluate(self, test_data: List[Dict], test_labels: np.ndarray) -> Dict:
        """Evaluate model performance"""
        predictions, probabilities = self.predict(test_data)
        
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        metrics = {
            'accuracy': accuracy_score(test_labels, predictions),
            'precision': precision_score(test_labels, predictions, zero_division=0),
            'recall': recall_score(test_labels, predictions, zero_division=0),
            'f1_score': f1_score(test_labels, predictions, zero_division=0),
        }
        
        logger.info(f"Evaluation metrics: {metrics}")
        return metrics