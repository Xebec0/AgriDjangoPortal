"""
Test cases for custom template tags
"""
from django.test import TestCase
from core.templatetags.custom_filters import get_item


class TemplateTagTests(TestCase):
    """Test custom template tags and filters"""
    
    def test_get_item_existing_key(self):
        """Test getting item from dictionary with existing key"""
        test_dict = {'name': 'John', 'age': 30}
        result = get_item(test_dict, 'name')
        self.assertEqual(result, 'John')
        
    def test_get_item_missing_key(self):
        """Test getting item from dictionary with missing key"""
        test_dict = {'name': 'John'}
        result = get_item(test_dict, 'age')
        self.assertEqual(result, '')
        
    def test_get_item_empty_dict(self):
        """Test getting item from empty dictionary"""
        test_dict = {}
        result = get_item(test_dict, 'key')
        self.assertEqual(result, '')
