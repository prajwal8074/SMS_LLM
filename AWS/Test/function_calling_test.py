from openai import OpenAI
import unittest
import sys
import os
from dotenv import load_dotenv
import json

load_dotenv()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import marketplace_tools

client = OpenAI(
	api_key=os.getenv("GEMINI_API_KEY"),
	base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class TestFunctionCall(unittest.TestCase):

	def setUp(self):
		"""
		Set up the test environment before each test method.
		Initializes self.listing_id to None, which will be set if a listing is added.
		"""
		print(f"\n--- Running test: {self._testMethodName} ---")
		self.listing_id = None # Initialize listing_id to None

	def tearDown(self):
		"""
		Clean up the test environment after each test method.
		Deletes the listing if it was created during the test.
		"""
		if self.listing_id:
			print(f"\n--- Deleting listing with ID: {self.listing_id} in tearDown ---")
			result = marketplace_tools.delete_listing_api(self.listing_id)
			print(f"Deletion result: {result}")
			self.assertEqual(result.get("status"), "success", "Failed to delete listing during tearDown.")
		print(f"\n--- Finished test: {self._testMethodName} ---")
	
	def test_non_call(self):
		messages = [{"role": "user", "content": "Hello"}]
		response = client.chat.completions.create(
			model="gemini-2.0-flash",
			messages=messages,
			tools=marketplace_tools.tools,
			tool_choice="auto"
		)
		print("\nChecking function call...\n")
		tool_calls = response.choices[0].message.tool_calls
		self.assertIsNone(tool_calls, response.choices[0].message.content)

	def test_add_listing(self):
		messages = [{"role": "user", "content": "I want to sell a vintage watch for $150. It's a gold-plated timepiece from the 1950s, in excellent working condition with a new leather strap."}]
		response = client.chat.completions.create(
			model="gemini-2.0-flash",
			messages=messages,
			tools=marketplace_tools.tools,
			tool_choice="auto"
		)
		print("\nChecking function call...\n")
		tool_calls = response.choices[0].message.tool_calls
		self.assertIsNotNone(tool_calls, response.choices[0].message.content)
		
		if tool_calls:
			function_name = tool_calls[0].function.name
			self.assertEqual(function_name, "add_listing")

			arguments_str = tool_calls[0].function.arguments
			try:
				function_args = json.loads(arguments_str)
			except json.JSONDecodeError as e:
				self.fail(f"Error parsing arguments for '{function_name}': {e}")
			
			add_listing_output = marketplace_tools.add_listing_api(**function_args)
			self.assertEqual(add_listing_output.get("status"), "success")
			self.listing_id = add_listing_output.get("listing_id")
			self.assertIsNotNone(self.listing_id, "Listing ID should not be None after adding listing.")

			print("\nCheck listing using get_all_listings tool...\n")
			
			actual_data = marketplace_tools.get_all_listings_api()
			expected_subset = function_args

			found_match = False
			for listing in actual_data['listings']:
				is_match = True
				for key, value in expected_subset.items():
					if key not in listing or listing[key] != value:
						is_match = False
						break
				
				if is_match:
					found_match = True
					print("\nListing found\n")
					break

			self.assertTrue(found_match, "No listing in the actual data contains the expected subset of values.")

			
			
if __name__ == '__main__':
	unittest.main()