import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL")
AUDIO_FILE_PATH = "AWS_Test_test.mp3"
FARMER_LANG = "hi-IN"  # test case in Hindi

def test_lambda_pipeline():
    # Read and encode the audio file
    with open(AUDIO_FILE_PATH, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    payload = {
        "audio_data": audio_base64,
        "farmer_language_code": FARMER_LANG
    }

    headers = {
        "Content-Type": "application/json"
    }

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
