import requests
import base64
import json
import os
from dotenv import load_dotenv
import unittest

API_GATEWAY_URL = "http://35.94.30.150:5002/process-voice"

class Test(unittest.TestCase):

	def setUp(self):
		"""
		Set up the test environment before each test method.
		"""
		print(f"\n--- Running test: {self._testMethodName} ---\n")
	
	def test_response_hindi_hindi(self):
		AUDIO_FILE_PATH = "hi.m4a"

		if not os.path.exists(AUDIO_FILE_PATH):
			print(f"Error: Audio file not found at {AUDIO_FILE_PATH}")
			return

		try:
			with open(AUDIO_FILE_PATH, "rb") as audio_file:
				audio_bytes = audio_file.read()
				audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

			payload = {
				"audio_data": audio_base64
			}

			headers = {
				"Content-Type": "application/json"
			}

			print(f"Sending audio from {AUDIO_FILE_PATH} to {API_GATEWAY_URL}...")
			response = requests.post(API_GATEWAY_URL, headers=headers, data=json.dumps(payload))
			self.assertEqual(response.status_code, 200, f"\n--- Error (Status Code: {response.status_code}) ---")
			if response.status_code == 200:
				print("\nChecking response...\n")
				result = response.json()
				self.assertIsNotNone(result.get('message'))
				self.assertIsNotNone(result.get('transcribed_text'))
				self.assertIsNotNone(result.get('llm_response'))
				self.assertIsNotNone(result.get('final_spoken_text'))
				self.assertIsNotNone(result.get('audio_response_base64'))
				print("\nChecking detected language...\n")
				self.assertEqual(result.get('detected_language'), 'hi-IN')
				print("\nChecking response language...\n")
				self.assertEqual(result.get('target_polly_lang'), 'hi-IN')
			else:
				print(response.text)

		except requests.exceptions.RequestException as e:
			print(f"Network or request error: {e}")
		except json.JSONDecodeError:
			print(f"Failed to decode JSON response: {response.text}")
		except Exception as e:
			print(f"An unexpected error occurred: {e}")

	def test_response_tamil_english(self):
		AUDIO_FILE_PATH = "ta.m4a"

		if not os.path.exists(AUDIO_FILE_PATH):
			print(f"Error: Audio file not found at {AUDIO_FILE_PATH}")
			return

		try:
			with open(AUDIO_FILE_PATH, "rb") as audio_file:
				audio_bytes = audio_file.read()
				audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

			payload = {
				"audio_data": audio_base64
			}

			headers = {
				"Content-Type": "application/json"
			}

			print(f"Sending audio from {AUDIO_FILE_PATH} to {API_GATEWAY_URL}...")
			response = requests.post(API_GATEWAY_URL, headers=headers, data=json.dumps(payload))
			self.assertEqual(response.status_code, 200, f"\n--- Error (Status Code: {response.status_code}) ---")
			if response.status_code == 200:
				print("\nChecking response...\n")
				result = response.json()
				self.assertIsNotNone(result.get('message'))
				self.assertIsNotNone(result.get('transcribed_text'))
				self.assertIsNotNone(result.get('llm_response'))
				self.assertIsNotNone(result.get('final_spoken_text'))
				self.assertIsNotNone(result.get('audio_response_base64'))
				print("\nChecking detected language...\n")
				self.assertEqual(result.get('detected_language'), 'ta-IN')
				print("\nChecking response language...\n")
				self.assertEqual(result.get('target_polly_lang'), 'en-IN')
			else:
				print(response.text)

		except requests.exceptions.RequestException as e:
			print(f"Network or request error: {e}")
		except json.JSONDecodeError:
			print(f"Failed to decode JSON response: {response.text}")
		except Exception as e:
			print(f"An unexpected error occurred: {e}")

	def test_response_gujarati_hindi(self):
		AUDIO_FILE_PATH = "gu.m4a"

		if not os.path.exists(AUDIO_FILE_PATH):
			print(f"Error: Audio file not found at {AUDIO_FILE_PATH}")
			return

		try:
			with open(AUDIO_FILE_PATH, "rb") as audio_file:
				audio_bytes = audio_file.read()
				audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

			payload = {
				"audio_data": audio_base64
			}

			headers = {
				"Content-Type": "application/json"
			}

			print(f"Sending audio from {AUDIO_FILE_PATH} to {API_GATEWAY_URL}...")
			response = requests.post(API_GATEWAY_URL, headers=headers, data=json.dumps(payload))
			self.assertEqual(response.status_code, 200, f"\n--- Error (Status Code: {response.status_code}) ---")
			if response.status_code == 200:
				print("\nChecking response...\n")
				result = response.json()
				self.assertIsNotNone(result.get('message'))
				self.assertIsNotNone(result.get('transcribed_text'))
				self.assertIsNotNone(result.get('llm_response'))
				self.assertIsNotNone(result.get('final_spoken_text'))
				self.assertIsNotNone(result.get('audio_response_base64'))
				print("\nChecking detected language...\n")
				self.assertEqual(result.get('detected_language'), 'gu-IN')
				print("\nChecking response language...\n")
				self.assertEqual(result.get('target_polly_lang'), 'hi-IN')
			else:
				print(response.text)

		except requests.exceptions.RequestException as e:
			print(f"Network or request error: {e}")
		except json.JSONDecodeError:
			print(f"Failed to decode JSON response: {response.text}")
		except Exception as e:
			print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
	unittest.main()