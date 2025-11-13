"""
Unit tests for FileAnalyzer
"""

import unittest
import tempfile
import os
from pathlib import Path
import time

from src.core.file_analyzer import FileAnalyzer


class TestFileAnalyzer(unittest.TestCase):
    """Test cases for FileAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = FileAnalyzer()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test file
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w') as f:
            f.write("Test content")
    
    def tearDown(self):
        """Clean up test fixtures"""
        try:
            os.remove(self.test_file)
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_extract_metadata(self):
        """Test metadata extraction"""
        metadata = self.analyzer.extract_metadata(self.test_file)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata['name'], 'test.txt')
        self.assertEqual(metadata['extension'], 'txt')
        self.assertGreater(metadata['size_bytes'], 0)
        self.assertIn('accessed_days_ago', metadata)
        self.assertIn('is_hidden', metadata)
    
    def test_nonexistent_file(self):
        """Test handling of nonexistent file"""
        result = self.analyzer.extract_metadata('/nonexistent/file.txt')
        self.assertIsNone(result)
    
    def test_statistics(self):
        """Test statistics tracking"""
        self.analyzer.extract_metadata(self.test_file)
        stats = self.analyzer.get_statistics()
        
        self.assertEqual(stats['files_analyzed'], 1)
        self.assertGreaterEqual(stats['success_rate'], 0)
    
    def test_hidden_file_detection(self):
        """Test hidden file detection"""
        hidden_file = os.path.join(self.temp_dir, ".hidden.txt")
        with open(hidden_file, 'w') as f:
            f.write("Hidden")
        
        metadata = self.analyzer.extract_metadata(hidden_file)
        self.assertTrue(metadata['is_hidden'])
        
        os.remove(hidden_file)


if __name__ == '__main__':
    unittest.main()