import requests
import base64
import json
import os

API_GATEWAY_URL = "https://7029iecp6i.execute-api.us-west-2.amazonaws.com/v1/process-voice"

AUDIO_FILE_PATH = "CallRecordings/caller_input.wav"
FARMER_LANGUAGE = "hi-IN"

def send_voice_to_gateway(audio_path, lang_code):
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return

    try:
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        payload = {
            "audio_data": audio_base64,
            "farmer_language_code": lang_code
        }

        headers = {
            "Content-Type": "application/json"
        }

        print(f"Sending audio from {audio_path} ({lang_code}) to {API_GATEWAY_URL}...")
        response = requests.post(API_GATEWAY_URL, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()
            print("\n--- Success ---")
            print(f"Message: {result.get('message')}")
            print(f"Transcribed Text: {result.get('transcribed_text')}")
            print(f"LLM Response: {result.get('llm_response')}")
            print(f"Final Spoken Text: {result.get('final_spoken_text')}")

            # Decode and save the audio response
            audio_response_base64 = result.get('audio_response_base64')
            if audio_response_base64:
                decoded_audio_bytes = base64.b64decode(audio_response_base64)
                output_audio_path = "output_response.mp3"
                with open(output_audio_path, "wb") as f:
                    f.write(decoded_audio_bytes)
                print(f"Received and saved audio response to {output_audio_path}")
            else:
                print("No audio response received.")

        else:
            print(f"\n--- Error (Status Code: {response.status_code}) ---")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Network or request error: {e}")
    except json.JSONDecodeError:
        print(f"Failed to decode JSON response: {response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    send_voice_to_gateway(AUDIO_FILE_PATH, FARMER_LANGUAGE)
