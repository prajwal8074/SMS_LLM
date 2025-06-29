import requests
import base64
import json
import os
from dotenv import load_dotenv
import unittest

load_dotenv()

API_GATEWAY_URL = os.getenv("API_GATEWAY_URL")

AUDIO_FILE_PATH = "test.mp3"
FARMER_LANGUAGE = "hi-IN"

class Test(unittest.TestCase):

    def test_send_voice_to_gateway(self):
        if not os.path.exists(AUDIO_FILE_PATH):
            print(f"Error: Audio file not found at {AUDIO_FILE_PATH}")
            return

        try:
            with open(AUDIO_FILE_PATH, "rb") as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

            payload = {
                "audio_data": audio_base64,
                "farmer_language_code": FARMER_LANGUAGE
            }

            headers = {
                "Content-Type": "application/json"
            }

            print(f"Sending audio from {AUDIO_FILE_PATH} ({FARMER_LANGUAGE}) to {API_GATEWAY_URL}...")
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