"""
End-to-end testing script for the AWS Lambda integration.
"""

import os
import json
import base64
from dotenv import load_dotenv
from farmer_helper import lambda_handler

# Load environment variables from .env for configuration
load_dotenv()

def encode_audio_to_base64(file_path):
    """
    Reads an audio file and encodes it as a base64 string.
    Args:
        file_path (str): Path to the audio file.
    Returns:
        str: Base64-encoded audio data.
    """
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def print_response(response):
    """
    Prints formatted Lambda response for debugging.
    Args:
        response (dict): Lambda function response.
    """
    print("✅ Lambda Response:")
    print(json.dumps(response, indent=2))

def run_e2e_test(audio_path, language_code):
    """
    Runs the end-to-end test for the Lambda handler.
    Args:
        audio_path (str): Path to the test audio file.
        language_code (str): Farmer's language code.
    """
    print(f"🔍 Loading and encoding audio: {audio_path}")
    audio_base64 = encode_audio_to_base64(audio_path)
    event = {
        "body": json.dumps({
            "audio_data": audio_base64,
            "farmer_language_code": language_code
        })
    }
    print("🔍 Running Lambda function...")
    response = lambda_handler(event, None)
    print_response(response)
    # Additional checks for response structure
    try:
        body = response.get('body')
        if body:
            resp_data = json.loads(body)
            assert 'transcribed_text' in resp_data
            assert 'llm_response' in resp_data
            assert 'audio_response_base64' in resp_data
            print("🎉 All expected fields present.")
        else:
            print("❌ No body in Lambda response.")
    except Exception as ex:
        print(f"❌ Error parsing Lambda response: {ex}")

if __name__ == "__main__":
    # Main test parameters
    test_audio = "AWS_Test_test.mp3"
    test_lang = "hi-IN"
    run_e2e_test(test_audio, test_lang)
    # Additional scenarios for coverage
    # 1. Test with a different language
    run_e2e_test(test_audio, "en-US")
    # 2. Test with a missing or empty audio file
    try:
        run_e2e_test("nonexistent.mp3", "hi-IN")
    except Exception as e:
        print(f"Handled missing file: {e}")
    # 3. Test with invalid language code
    run_e2e_test(test_audio, "invalid-code")
    # 4. Test with empty audio content
    empty_audio_path = "empty_test.mp3"
    with open(empty_audio_path, "wb") as f:
        f.write(b'')
    run_e2e_test(empty_audio_path, "hi-IN")
    os.remove(empty_audio_path)
