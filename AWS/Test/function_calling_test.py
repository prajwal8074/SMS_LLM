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

	def test_non_call(self):
		# Non calling test
		print("\nNon calling test\n")
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
		print("\nTest add_listing tool using function calling...\n")
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

			marketplace_tools.process_tool_calls(response)

			print("\nCheck listing using get_all_listings tool...\n")
			arguments_str = tool_calls[0].function.arguments

			try:
				function_args = json.loads(arguments_str)
			except json.JSONDecodeError as e:
				print(f"  Error parsing arguments for '{function_name}': {e}")
			
			actual_data = marketplace_tools.get_all_listings_api()
			expected_subset = function_args

			found_match = False
			for listing in actual_data['listings']:
				# Check if all key-value pairs from expected_subset are present and match in the current listing
				is_match = True
				for key, value in expected_subset.items():
					if key not in listing or listing[key] != value:
						is_match = False
						break # Break from inner loop if a mismatch is found
				
				if is_match:
					found_match = True
					print("\nListing found\n")
					break # Break from outer loop if a match is found

			self.assertTrue(found_match, "No listing in the actual data contains the expected subset of values.")

if __name__ == '__main__':
	unittest.main()