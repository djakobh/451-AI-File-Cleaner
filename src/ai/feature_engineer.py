"""
Feature engineering for ML models
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from sklearn.preprocessing import LabelEncoder, StandardScaler
import logging

from ..core.config import FEATURE_CONFIG

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Prepares features from file metadata for ML models"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = []
        self.is_fitted = False
    
    def prepare_features(self, file_data: List[Dict], fit: bool = False) -> pd.DataFrame:
        """
        Convert file metadata to ML-ready features
        
        Args:
            file_data: List of file metadata dictionaries
            fit: Whether to fit scalers and encoders
            
        Returns:
            DataFrame with engineered features
        """
        if not file_data:
            logger.warning("No file data provided for feature preparation")
            return pd.DataFrame()
        
        df = pd.DataFrame(file_data)
        
        # === Numeric Features ===
        features = pd.DataFrame()
        
        # Size features
        features['size_mb'] = df['size_mb']
        features['log_size'] = np.log1p(df['size_mb'])  # Log transform for skewed distribution
        
        # Time-based features
        features['created_days_ago'] = df['created_days_ago']
        features['modified_days_ago'] = df['modified_days_ago']
        features['accessed_days_ago'] = df['accessed_days_ago']
        
        # Derived time features
        features['days_since_modification'] = df['modified_days_ago']
        features['days_since_access'] = df['accessed_days_ago']
        features['dormant_period'] = df['accessed_days_ago'] - df['modified_days_ago']
        
        # Access patterns
        features['access_to_modify_ratio'] = df.get('access_to_modify_ratio', 
                                                     df['accessed_days_ago'] / np.maximum(df['modified_days_ago'], 0.1))
        features['is_stale'] = (df['accessed_days_ago'] > FEATURE_CONFIG['access_threshold_days']).astype(int)
        
        # === Categorical Features (Boolean) ===
        features['is_hidden'] = df['is_hidden'].astype(int)
        features['is_disposable_ext'] = df['is_disposable_ext'].astype(int)
        features['in_system_folder'] = df['in_system_folder'].astype(int)
        features['is_recent'] = df.get('is_recent', df['accessed_days_ago'] < 7).astype(int)
        features['is_old'] = df.get('is_old', df['modified_days_ago'] > 365).astype(int)
        features['is_large'] = df.get('is_large', df['size_mb'] > 100).astype(int)
        
        # === Path-based Features ===
        features['depth'] = df['depth']
        features['depth_normalized'] = np.minimum(df['depth'] / 10, 1.0)  # Cap at 1.0
        
        # === Size Categories ===
        size_bins = FEATURE_CONFIG['size_bins']
        features['size_category'] = pd.cut(
            df['size_mb'],
            bins=size_bins,
            labels=range(len(size_bins) - 1),
            include_lowest=True
        ).astype(int)
        
        # === Extension Encoding ===
        if 'extension' in df.columns:
            if fit or 'extension' not in self.label_encoders:
                # Fit encoder on unique extensions
                unique_extensions = df['extension'].unique().tolist()
                self.label_encoders['extension'] = LabelEncoder()
                self.label_encoders['extension'].fit(unique_extensions + ['unknown'])
            
            try:
                features['extension_encoded'] = self.label_encoders['extension'].transform(df['extension'])
            except ValueError:
                # Handle unknown extensions
                features['extension_encoded'] = 0
                logger.warning("Unknown extensions found, using default encoding")
        
        # === Category Encoding ===
        if 'category' in df.columns:
            if fit or 'category' not in self.label_encoders:
                unique_categories = df['category'].unique().tolist()
                self.label_encoders['category'] = LabelEncoder()
                self.label_encoders['category'].fit(unique_categories + ['unknown'])
            
            try:
                features['category_encoded'] = self.label_encoders['category'].transform(df['category'])
            except ValueError:
                features['category_encoded'] = 0
        
        # === Interaction Features ===
        features['size_age_interaction'] = features['size_mb'] * features['accessed_days_ago']
        features['large_and_old'] = (features['is_large'] * features['is_old']).astype(int)
        features['small_and_recent'] = ((features['size_mb'] < 1) * features['is_recent']).astype(int)
        
        # === Statistical Features ===
        if len(df) > 1:
            # Relative size (compared to median)
            median_size = df['size_mb'].median()
            features['size_relative'] = df['size_mb'] / max(median_size, 0.1)
            
            # Relative access age
            median_access = df['accessed_days_ago'].median()
            features['access_relative'] = df['accessed_days_ago'] / max(median_access, 1)
        else:
            features['size_relative'] = 1.0
            features['access_relative'] = 1.0
        
        # Store feature names
        self.feature_names = features.columns.tolist()
        
        # Mark as fitted
        if fit:
            self.is_fitted = True
        
        logger.debug(f"Prepared {len(features)} samples with {len(features.columns)} features")
        
        return features
    
    def scale_features(self, features: pd.DataFrame, fit: bool = False) -> np.ndarray:
        """
        Scale features using StandardScaler
        
        Args:
            features: DataFrame of features
            fit: Whether to fit the scaler
            
        Returns:
            Scaled feature array
        """
        if features.empty:
            return np.array([])
        
        if fit:
            scaled = self.scaler.fit_transform(features)
            logger.debug("Fitted and transformed features")
        else:
            if not self.is_fitted:
                logger.warning("Scaler not fitted, fitting now")
                scaled = self.scaler.fit_transform(features)
            else:
                scaled = self.scaler.transform(features)
        
        return scaled
    
    def get_feature_importance_names(self) -> List[str]:
        """Get list of feature names for importance analysis"""
        return self.feature_names
    
    def prepare_and_scale(self, file_data: List[Dict], fit: bool = False) -> np.ndarray:
        """
        Convenience method to prepare and scale in one step
        
        Args:
            file_data: List of file metadata dictionaries
            fit: Whether to fit scalers and encoders
            
        Returns:
            Scaled feature array
        """
        features = self.prepare_features(file_data, fit=fit)
        if features.empty:
            return np.array([])
        return self.scale_features(features, fit=fit)