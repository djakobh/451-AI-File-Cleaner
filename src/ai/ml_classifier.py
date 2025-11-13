"""
Machine Learning classifier for file importance prediction
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
        Generate synthetic training data based on heuristics
        
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
            size_mb = np.random.lognormal(0, 2)  # Log-normal distribution for file sizes
            created_days = np.random.uniform(1, 1000)
            accessed_days = np.random.uniform(0, created_days)
            modified_days = np.random.uniform(accessed_days, created_days)
            
            # Random file type
            is_disposable = np.random.choice([True, False], p=[0.3, 0.7])
            is_hidden = np.random.choice([True, False], p=[0.1, 0.9])
            
            # Depth (shallower files more common)
            depth = int(np.random.exponential(3) + 2)
            
            # === Labeling Heuristic ===
            # Start with KEEP (1)
            label = 1
            
            # DELETE (0) if meets certain criteria
            delete_score = 0
            
            # Disposable extensions are likely deletable
            if is_disposable:
                delete_score += 3
            
            # Not accessed in 6 months
            if accessed_days > FEATURE_CONFIG['access_threshold_days']:
                delete_score += 2
            
            # Large and old
            if size_mb > FEATURE_CONFIG['large_file_threshold_mb'] and accessed_days > 90:
                delete_score += 2
            
            # Very old files
            if modified_days > FEATURE_CONFIG['old_file_threshold_days']:
                delete_score += 1
            
            # Hidden files that are old
            if is_hidden and accessed_days > 90:
                delete_score += 1
            
            # Decide based on score
            if delete_score >= 3:
                label = 0  # DELETE
            
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
                'in_system_folder': False,  # Never train on system files
                'days_since_modification': modified_days,
                'days_since_access': accessed_days,
                'access_to_modify_ratio': accessed_days / max(modified_days, 0.1),
                'is_recent': accessed_days < 7,
                'is_old': modified_days > 365,
                'is_large': size_mb > 100,
                'extension': 'tmp' if is_disposable else 'dat',
                'category': 'disposable' if is_disposable else 'other',
            }
            
            synthetic_data.append(file_metadata)
            labels.append(label)
        
        logger.info(f"Generated synthetic data: {sum(labels)} KEEP, {len(labels) - sum(labels)} DELETE")
        
        return synthetic_data, np.array(labels)
    
    def train(self, file_data: Optional[List[Dict]] = None, labels: Optional[np.ndarray] = None):
        """
        Train the classifier
        
        Args:
            file_data: Training file metadata (if None, uses synthetic data)
            labels: Training labels (if None, uses synthetic labels)
        """
        logger.info("Training ML classifier...")
        
        # Use synthetic data if no training data provided
        if file_data is None or labels is None:
            file_data, labels = self.generate_synthetic_data()
        
        # Prepare features
        features = self.feature_engineer.prepare_features(file_data, fit=True)
        X_scaled = self.feature_engineer.scale_features(features, fit=True)
        
        # Train model
        self.model.fit(X_scaled, labels)
        self.is_trained = True
        
        # Calculate training accuracy
        train_accuracy = self.model.score(X_scaled, labels)
        logger.info(f"Training complete. Accuracy: {train_accuracy:.2%}")
        
        # Feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_names = self.feature_engineer.get_feature_importance_names()
            importances = self.model.feature_importances_
            
            # Log top 10 features
            top_indices = np.argsort(importances)[-10:][::-1]
            logger.info("Top 10 important features:")
            for idx in top_indices:
                if idx < len(feature_names):
                    logger.info(f"  {feature_names[idx]}: {importances[idx]:.4f}")
        
        # Save model
        self.save_model()
    
    def predict(self, file_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict file importance
        
        Args:
            file_data: List of file metadata dictionaries
            
        Returns:
            Tuple of (predictions, probabilities)
            - predictions: 1 = KEEP, 0 = DELETE
            - probabilities: [prob_delete, prob_keep] for each file
        """
        if not self.is_trained:
            logger.warning("Model not trained, training on synthetic data now")
            self.train()
        
        if not file_data:
            return np.array([]), np.array([])
        
        # Prepare features
        features = self.feature_engineer.prepare_features(file_data, fit=False)
        X_scaled = self.feature_engineer.scale_features(features, fit=False)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        logger.debug(f"Predicted {len(predictions)} files: "
                    f"{sum(predictions)} KEEP, {len(predictions) - sum(predictions)} DELETE")
        
        return predictions, probabilities
    
    def predict_single(self, file_metadata: Dict) -> Tuple[int, float]:
        """
        Predict importance for a single file
        
        Args:
            file_metadata: Single file metadata dictionary
            
        Returns:
            Tuple of (prediction, confidence)
        """
        predictions, probabilities = self.predict([file_metadata])
        
        if len(predictions) > 0:
            pred = int(predictions[0])
            confidence = float(probabilities[0][pred])
            return pred, confidence
        
        return 1, 0.5  # Default to KEEP with low confidence
    
    def save_model(self):
        """Save trained model and feature engineer"""
        if not self.is_trained:
            logger.warning("Cannot save untrained model")
            return
        
        try:
            # Save model
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Save feature engineer
            with open(self.feature_engineer_path, 'wb') as f:
                pickle.dump(self.feature_engineer, f)
            
            logger.info(f"Model saved to {self.model_path}")
        
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load_model(self) -> bool:
        """
        Load trained model and feature engineer
        
        Returns:
            True if successful, False otherwise
        """
        if not self.model_path.exists() or not self.feature_engineer_path.exists():
            logger.debug("No saved model found")
            return False
        
        try:
            # Load model
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load feature engineer
            with open(self.feature_engineer_path, 'rb') as f:
                self.feature_engineer = pickle.load(f)
            
            self.is_trained = True
            logger.info(f"Model loaded from {self.model_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def evaluate(self, test_data: List[Dict], test_labels: np.ndarray) -> Dict:
        """
        Evaluate model performance
        
        Args:
            test_data: Test file metadata
            test_labels: True labels
            
        Returns:
            Dictionary of evaluation metrics
        """
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