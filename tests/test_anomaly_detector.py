"""
Unit tests for AnomalyDetector
"""

import unittest
import numpy as np

from src.ai.anomaly_detector import AnomalyDetector


class TestAnomalyDetector(unittest.TestCase):
    """Test cases for AnomalyDetector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.detector = AnomalyDetector()
    
    def generate_test_data(self, n_samples=100):
        """Generate test file data"""
        data = []
        for i in range(n_samples):
            data.append({
                'size_mb': np.random.lognormal(0, 1),
                'accessed_days_ago': np.random.uniform(0, 365),
                'modified_days_ago': np.random.uniform(0, 365),
                'depth': np.random.randint(2, 10),
            })
        
        # Add some obvious anomalies
        data.append({
            'size_mb': 10000,  # Very large
            'accessed_days_ago': 1000,  # Not accessed in long time
            'modified_days_ago': 1000,
            'depth': 20,  # Very deep
        })
        
        return data
    
    def test_fit(self):
        """Test fitting the detector"""
        data = self.generate_test_data()
        self.detector.fit(data)
        self.assertTrue(self.detector.is_fitted)
    
    def test_detect(self):
        """Test anomaly detection"""
        data = self.generate_test_data()
        anomalies = self.detector.detect(data)
        
        self.assertEqual(len(anomalies), len(data))
        self.assertTrue(all(a in [0, 1] for a in anomalies))
        
        # Should detect at least the obvious anomaly we added
        self.assertGreater(sum(anomalies), 0)
    
    def test_detect_with_reasons(self):
        """Test anomaly detection with reasons"""
        data = self.generate_test_data(10)
        results = self.detector.detect_with_reasons(data)
        
        self.assertEqual(len(results), len(data))
        for result in results:
            self.assertIn('is_anomaly', result)
            self.assertIn('anomaly_score', result)
            self.assertIn('reasons', result)


if __name__ == '__main__':
    unittest.main()