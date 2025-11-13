"""
Unit tests for MLClassifier
"""

import unittest
import numpy as np

from src.ai.ml_classifier import MLClassifier


class TestMLClassifier(unittest.TestCase):
    """Test cases for MLClassifier"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.classifier = MLClassifier()
    
    def test_synthetic_data_generation(self):
        """Test synthetic data generation"""
        data, labels = self.classifier.generate_synthetic_data(n_samples=100)
        
        self.assertEqual(len(data), 100)
        self.assertEqual(len(labels), 100)
        self.assertTrue(all(isinstance(d, dict) for d in data))
        self.assertTrue(all(l in [0, 1] for l in labels))
    
    def test_training(self):
        """Test model training"""
        self.classifier.train()
        self.assertTrue(self.classifier.is_trained)
    
    def test_prediction(self):
        """Test prediction on sample data"""
        # Generate test data
        test_data = [{
            'size_mb': 100,
            'size_bytes': 100 * 1024 * 1024,
            'size_kb': 100 * 1024,
            'created_days_ago': 365,
            'modified_days_ago': 365,
            'accessed_days_ago': 365,
            'is_hidden': False,
            'depth': 5,
            'is_disposable_ext': True,
            'in_system_folder': False,
            'days_since_modification': 365,
            'days_since_access': 365,
            'access_to_modify_ratio': 1.0,
            'is_recent': False,
            'is_old': True,
            'is_large': True,
            'extension': 'tmp',
            'category': 'disposable',
        }]
        
        predictions, probabilities = self.classifier.predict(test_data)
        
        self.assertEqual(len(predictions), 1)
        self.assertEqual(len(probabilities), 1)
        self.assertIn(predictions[0], [0, 1])
        self.assertAlmostEqual(sum(probabilities[0]), 1.0, places=5)
    
    def test_feature_importance(self):
        """Test that feature importance is calculated"""
        self.classifier.train()
        
        if hasattr(self.classifier.model, 'feature_importances_'):
            importances = self.classifier.model.feature_importances_
            self.assertGreater(len(importances), 0)
            self.assertAlmostEqual(sum(importances), 1.0, places=5)


if __name__ == '__main__':
    unittest.main()