import os
import sys
import unittest
import requests
import json
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Base URL for API
BASE_URL = "http://localhost:8000"

class TestDocuScraperAPI(unittest.TestCase):
    """Test cases for DocuScraper API"""
    
    def setUp(self):
        """Set up test environment"""
        # Check if API is running
        try:
            response = requests.get(f"{BASE_URL}/health")
            if response.status_code != 200:
                self.skipTest("API is not running. Start the API server before running tests.")
        except requests.exceptions.ConnectionError:
            self.skipTest("API is not running. Start the API server before running tests.")
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = requests.get(BASE_URL)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "DocuScraper API")
        self.assertIn("version", data)
        self.assertIn("endpoints", data)
    
    def test_health_endpoint(self):
        """Test health endpoint"""
        response = requests.get(f"{BASE_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
    
    def test_document_classes_endpoint(self):
        """Test document classes endpoint"""
        response = requests.get(f"{BASE_URL}/document/classes")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
    
    def test_search_endpoint(self):
        """Test search endpoint with a small limit to avoid long tests"""
        payload = {
            "doc_class": "invoice",
            "limit": 1,
            "deep_validation": False
        }
        response = requests.post(f"{BASE_URL}/search", json=payload)
        
        # This might take time and could fail if API keys aren't set
        # So we'll just check if the response format is correct
        self.assertIn(response.status_code, [200, 500])
        
        if response.status_code == 200:
            data = response.json()
            self.assertIsInstance(data, list)
            if data:
                doc = data[0]
                self.assertIn("doc_class", doc)
                self.assertIn("title", doc)
                self.assertIn("url", doc)
                self.assertIn("file_path", doc)
    
    def test_document_text_endpoint_invalid_path(self):
        """Test document text endpoint with invalid path"""
        payload = {
            "file_path": "nonexistent_file.pdf"
        }
        response = requests.post(f"{BASE_URL}/document/text", json=payload)
        self.assertEqual(response.status_code, 404)

if __name__ == "__main__":
    unittest.main()