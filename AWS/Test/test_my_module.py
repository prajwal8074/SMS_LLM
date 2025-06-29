# AWS/Test/test_my_module.py
import unittest
import sys
import os

# Adjusting the path to include the 'AWS' directory (parent of 'Test')
# This path manipulation is crucial for the test file to find my_module.py
# Explanation:
# os.path.dirname(__file__)       -> AWS/Test/
# os.path.join(..., '..')         -> AWS/
# os.path.abspath(...)            -> /path/to/SMS_LLM/AWS/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now, import my_module directly as it's within 'AWS/' which is on the path
from my_module import add, subtract

class TestMyModule(unittest.TestCase):

    def test_add(self):
        self.assertEqual(add(2, 3), 4)
        self.assertEqual(add(-1, 1), 0)
        self.assertEqual(add(0, 0), 0)

    def test_subtract(self):
        self.assertEqual(subtract(5, 2), 3)
        self.assertEqual(subtract(2, 5), -3)
        self.assertEqual(subtract(0, 0), 0)

if __name__ == '__main__':
    unittest.main()