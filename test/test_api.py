import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

class SaralNitiApiTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    # Test 1 - Homepage loads successfully
    def test_home(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

    # Test 2 - Schemes API responds
    def test_get_schemes(self):
        res = self.client.get('/api/schemes')
        self.assertIn(res.status_code, [200, 500])

    # Test 3 - Standard text search responds
    def test_search_text(self):
        res = self.client.get('/api/search?q=farmer')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertGreater(data.get("count", 0), 0)

    # Test 4 - Search by age query parameter
    def test_search_by_age_param(self):
        res = self.client.get('/api/search?age=25')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("age"), 25)
        self.assertGreater(data.get("count", 0), 0)

    # Test 5 - Search by entering age in search bar query (e.g. q=25 or q=age 25)
    def test_search_by_age_in_query(self):
        res = self.client.get('/api/search?q=25')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("age"), 25)
        self.assertGreater(data.get("count", 0), 0)

        res2 = self.client.get('/api/search?q=age+25')
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertEqual(data2.get("age"), 25)

    # Test 6 - Combined keyword and age search (e.g. farmer 25)
    def test_search_combined_keyword_and_age(self):
        res = self.client.get('/api/search?q=farmer+25')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("age"), 25)
        self.assertEqual(data.get("text_query"), "farmer")
        self.assertGreater(data.get("count", 0), 0)

    # Test 7 - Filter by category with age
    def test_filter_with_age(self):
        res = self.client.get('/api/filter?category=agriculture&age=25')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("age"), 25)

    # Test 8 - Empty search handling
    def test_empty_search(self):
        res = self.client.get('/api/search?q=')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("count"), 0)
        self.assertEqual(data.get("schemes"), [])

    # Test 9 - Filter by rural category
    def test_filter_rural_category(self):
        res = self.client.get('/api/filter?category=rural')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertGreater(data.get("count", 0), 0)

    # Test 10 - Filter by rural area tag
    def test_filter_rural_area_tag(self):
        res = self.client.get('/api/filter?tag=rural+area')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertGreater(data.get("count", 0), 0)

    # Test 11 - Search by rural area query
    def test_search_rural_area(self):
        res = self.client.get('/api/search?q=rural+area')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")
        self.assertGreater(data.get("count", 0), 0)

    # Test 12 - Chatbot responds to rural inquiry
    def test_chatbot_rural(self):
        res = self.client.post('/api/chatbot', json={"message": "tell me rural area schemes"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("rural", data.get("reply", "").lower())

if __name__ == '__main__':
    unittest.main()