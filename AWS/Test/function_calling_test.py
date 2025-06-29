from openai import OpenAI
import unittest
import sys
import os
from dotenv import load_dotenv

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
		messages = [{"role": "user", "content": "Hello"}]
		response = client.chat.completions.create(
			model="gemini-2.0-flash",
			messages=messages,
			tools=marketplace_tools.tools,
			tool_choice="auto"
		)
		tool_calls = response.choices[0].message.tool_calls
		self.assertIsNone(tool_calls, response.choices[0].message.content)

	def test_call(self):
		# Non calling test
		messages = [{"role": "user", "content": "I want to sell a vintage watch for $150. It's a gold-plated timepiece from the 1950s, in excellent working condition with a new leather strap."}]
		response = client.chat.completions.create(
			model="gemini-2.0-flash",
			messages=messages,
			tools=marketplace_tools.tools,
			tool_choice="auto"
		)
		tool_calls = response.choices[0].message.tool_calls
		self.assertIsNotNone(tool_calls, response.choices[0].message.content)
	

if __name__ == '__main__':
	unittest.main()