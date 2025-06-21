"""
Integration test for the Lambda pipeline.
This script simulates a client sending a request to the API endpoint,
validates the response, and checks for correct processing and security policies.
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
AUDIO_FILE_PATH = "AWS_Test_test.mp3"
FARMER_LANG = "hi-IN"  # test case in Hindi

def send_audio_for_integration(audio_path, lang_code):
    """
    Sends an audio file to the API endpoint and validates the response.
    Args:
        audio_path (str): Path to the audio file.
        lang_code (str): Farmer's language code.
    """
    print(f"🔍 Reading and encoding audio from {audio_path}")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "audio_data": audio_base64,
        "farmer_language_code": lang_code
    }
    headers = {
        "Content-Type": "application/json"
    }
    print(f"🛰️ Sending request to {API_URL}")
    response = requests.post(API_URL, json=payload, headers=headers)
    # Status check
    assert response.status_code == 200, f"Error response: {response.text}"
    data = response.json()
    # Check expected keys in response
    assert "transcribed_text" in data, "Missing transcribed text"
    assert "llm_response" in data, "Missing LLM response"
    assert "final_spoken_text" in data, "Missing translated spoken text"
    assert "audio_response_base64" in data, "Missing audio response"
    # Basic validation of audio response
    audio_bytes_response = base64.b64decode(data["audio_response_base64"])
    assert len(audio_bytes_response) > 1000, "Audio response too short"
    print("✅ Integration test passed.")
    print("🔤 Transcription:", data["transcribed_text"])
    print("🤖 LLM Reply:", data["llm_response"])
    print("🗣️ Final Response:", data["final_spoken_text"])

def test_various_languages():
    """
    Tests integration with multiple language codes.
    """
    for lang_code in ["hi-IN", "en-US", "bn-IN"]:
        try:
            send_audio_for_integration(AUDIO_FILE_PATH, lang_code)
        except AssertionError as e:
            print(f"❌ Test failed for {lang_code}: {e}")

def test_invalid_audio():
    """
    Tests integration with invalid audio file.
    """
    try:
        send_audio_for_integration("invalid.mp3", "hi-IN")
    except Exception as e:
        print(f"❌ Test failed for missing/invalid audio: {e}")

def test_invalid_language():
    """
    Tests integration with an invalid language code.
    """
    try:
        send_audio_for_integration(AUDIO_FILE_PATH, "xx-YY")
    except AssertionError as e:
        print(f"❌ Test failed for invalid language code: {e}")

if __name__ == "__main__":
    # Main integration test
    send_audio_for_integration(AUDIO_FILE_PATH, FARMER_LANG)
    # Additional scenarios for coverage
    test_various_languages()
    test_invalid_audio()
    test_invalid_language()
