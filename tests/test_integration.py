"""
Integration tests for the complete system
"""

import unittest
import tempfile
import os

from src.core.file_analyzer import FileAnalyzer
from src.core.scanner import DirectoryScanner
from src.ai.ml_classifier import MLClassifier
from src.ai.anomaly_detector import AnomalyDetector
from src.ai.recommender import RecommendationEngine


class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.test_files = []
        for i in range(10):
            filepath = os.path.join(self.temp_dir, f"test_{i}.txt")
            with open(filepath, 'w') as f:
                f.write(f"Test content {i}")
            self.test_files.append(filepath)
    
    def tearDown(self):
        """Clean up"""
        for filepath in self.test_files:
            try:
                os.remove(filepath)
            except:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_full_pipeline(self):
        """Test complete analysis pipeline"""
        # 1. Scan directory
        analyzer = FileAnalyzer()
        scanner = DirectoryScanner(analyzer)
        file_data = scanner.scan(self.temp_dir, max_files=20)
        
        self.assertGreater(len(file_data), 0)
        
        # 2. ML Classification
        classifier = MLClassifier()
        predictions, probabilities = classifier.predict(file_data)
        
        self.assertEqual(len(predictions), len(file_data))
        
        # 3. Anomaly Detection
        detector = AnomalyDetector()
        anomalies = detector.detect(file_data)
        
        self.assertEqual(len(anomalies), len(file_data))
        
        # 4. Recommendations
        recommender = RecommendationEngine()
        recommendations = recommender.get_recommendations(
            file_data,
            predictions.tolist(),
            probabilities.tolist()
        )
        
        self.assertEqual(len(recommendations), len(file_data))
        
        # Verify recommendation structure
        for rec in recommendations:
            self.assertIn('recommend_delete', rec)
            self.assertIn('confidence', rec)
            self.assertIn('ml_prediction', rec)


if __name__ == '__main__':
    unittest.main()