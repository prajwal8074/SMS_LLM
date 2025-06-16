import os
import json
import base64
from dotenv import load_dotenv
from farmer_helper import lambda_handler

# Load environment variables from .env
load_dotenv()

def encode_audio_to_base64(file_path):
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

audio_base64 = encode_audio_to_base64("AWS_Test_test.mp3")

event = {
    "body": json.dumps({
        "audio_data": audio_base64,
        "farmer_language_code": "hi-IN"
    })
}

print("🔍 Running Lambda function...")
response = lambda_handler(event, None)

print("✅ Lambda Response:")
print(json.dumps(response, indent=2))
