# Voice Processing Gateway for Agricultural Assistance

This AWS Lambda function processes voice inputs from farmers, generates AI responses using Gemini, and returns audio responses. The system handles multilingual conversations using AWS Transcribe, Translate, and Polly services.

## Demo Video
https://github.com/user-attachments/assets/17e0aef0-bae6-435f-b930-706cfd088f27

## Process
![process](https://github.com/user-attachments/assets/5c39c36b-e3a8-4c67-8f65-d6130d45ee48)

# Voice Processing Gateway for Agricultural Assistance

This AWS Lambda function processes voice inputs from farmers, generates AI responses using Gemini, and returns audio responses. The system handles multilingual conversations using AWS Transcribe, Translate, and Polly services.

## Demo Video
https://github.com/user-attachments/assets/17e0aef0-bae6-435f-b930-706cfd088f27

## Process
![process](https://github.com/user-attachments/assets/5c39c36b-e3a8-4c67-8f65-d6130d45ee48)

# Farm Assist Voice Gateway

A serverless voice gateway solution for agricultural assistance, leveraging AWS services and AI technologies.

## Key AWS Services Used

- **AWS CloudFormation**: For Infrastructure as Code (IaC), allowing declarative provisioning and management of all AWS resources.
- **AWS Lambda**: Serverless compute for the core application logic.
- **Amazon API Gateway**: A fully managed service to create, publish, maintain, monitor, and secure APIs.
- **Amazon S3**: Scalable object storage for audio and transcription data.
- **Amazon Transcribe**: Automated speech recognition (ASR) service.
- **Amazon Translate**: Neural machine translation service.
- **Amazon Polly**: Text-to-Speech (TTS) service with natural-sounding voices.
- **AWS IAM**: Manages access and permissions across AWS services.
- **Amazon CloudWatch**: For logging and monitoring.

## Deployment Guide

This project is deployed using AWS CloudFormation, which simplifies the provisioning and management of your AWS infrastructure.

### Prerequisites

Before you begin, ensure you have:

- An AWS Account with sufficient permissions to create IAM Roles, Lambda Functions, S3 Buckets, and API Gateways.
- An API Key for Google Gemini LLM.
- An API Key for ElevenLabs Text-to-Speech (if you plan to use ElevenLabs voices).
- AWS CLI installed and configured (optional, but useful for advanced management).

### Steps to Deploy

1. **Save the CloudFormation Template**:
   - Copy the entire YAML content from the voice-gateway-cloudformation immersive document.
   - Save it to a file named `voice-gateway-stack.yaml` on your local machine.

2. **Create a CloudFormation Stack**:
   - Log in to the AWS Management Console and navigate to CloudFormation.
   - Click on "Create stack" > "With new resources (standard)".

3. **Specify Template**:
   - On the "Specify template" page, select "Template is ready".
   - Choose "Upload a template file" and click "Choose file". Select your `voice-gateway-stack.yaml` file.
   - Click "Next".

4. **Specify Stack Details**:
   - Stack name: Provide a unique name for your CloudFormation stack (e.g., `FarmAssistVoiceGatewayStack`).
   - Parameters: You will be prompted to enter values for the following parameters:
     - `BucketNamePrefix`: Enter a unique prefix for your S3 bucket (e.g., `farm-assist-audio`).
     - `GeminiApiKey`: Paste your Google Gemini API Key here.
     - `ElevenLabsApiKey`: Paste your ElevenLabs API Key here.
     - `LambdaMemory`: (Optional) Adjust the memory for your Lambda function (default: 512 MB).
     - `LambdaTimeout`: (Optional) Adjust the timeout for your Lambda function (default: 90 seconds).
   - Click "Next".

5. **Configure Stack Options**:
   - You can optionally add tags (key-value pairs) for resource organization and cost tracking.
   - Leave other options at their defaults for now.
   - Click "Next".

6. **Review and Create**:
   - Review all the details of the stack.
   - **Important**: Scroll to the bottom and check the box: "I acknowledge that AWS CloudFormation might create IAM resources with custom names."
   - Click "Create stack".

7. **Monitor Deployment**:
   - CloudFormation will now start creating all the resources defined in the template.
   - You can monitor the deployment progress in the "Events" tab of your CloudFormation stack.
   - Wait until the stack status shows `CREATE_COMPLETE`.

## Post-Deployment

Once the CloudFormation stack is successfully deployed:

1. **Retrieve Outputs**: Go to the "Outputs" tab of your CloudFormation stack.
   - `S3BucketName`: Name of the S3 bucket created for your audio files.
   - `ApiGatewayInvokeURL`: URL of your API Gateway endpoint (e.g., `https://<unique-id>.execute-api.<your-region>.amazonaws.com/v1/process-voice`).

## Testing the Gateway

You can use a simple Python script to test your deployed Voice Gateway.

### Prerequisites for Testing

- Python 3.x installed on your local machine.
- The `requests` library installed (`pip install requests`).
- A small `.mp3` (or `.wav`) audio file with spoken content.

### Test Script (`test_gateway.py`)

Create a file named `test_gateway.py` with the following content:

```python
import requests
import base64
import json
import os

# --- Configuration for testing ---
API_GATEWAY_URL = "YOUR_API_GATEWAY_INVOKE_URL_HERE" # <<< REPLACE THIS!
# Path to your audio file (ensure it's MP3 or WAV)
AUDIO_FILE_PATH = "path/to/your/test_audio.mp3" # <<< REPLACE THIS!
FARMER_LANGUAGE = "hi-IN" # Set the expected language code for the audio

def send_voice_to_gateway(audio_path, lang_code):
    """Reads an audio file, encodes it, and sends it to the API Gateway."""
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
            print(f"Detected Language: {result.get('detected_language')}")

            # Decode and save the audio response
            audio_response_base64 = result.get('audio_response_base64')
            if audio_response_base64:
                decoded_audio_bytes = base64.b64decode(audio_response_base64)
                output_audio_path = "output_response.mp3"
                with open(output_audio_path, "wb") as f:
                    f.write(decoded_audio_bytes)
                print(f"Received and saved AI's spoken response to {output_audio_path}")
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

# Run the test
if __name__ == "__main__":
    send_voice_to_gateway(AUDIO_FILE_PATH, FARMER_LANGUAGE)
```
## How to Run the Test Script

### Update Placeholders
1. In `test_gateway.py`:
   - Replace `YOUR_API_GATEWAY_INVOKE_URL_HERE` with your actual API Gateway URL
   - Replace `path/to/your/test_audio.mp3` with your audio file path

### Execute the Script
```bash
python test_gateway.py
```
## Test Script Output and Debugging

### Expected Output
After successfully running the test script, you'll see the following information printed in your terminal:
- **Transcribed text**: The converted text from your audio input
- **LLM response**: The generated response from Google Gemini
- **Final spoken text**: The text that was converted to speech
- **Detected language**: The language identified in the audio input

Additionally:
- The AI's spoken response will be saved as `output_response.mp3` in your current working directory
- You can play this file to verify the audio quality and response accuracy

### Troubleshooting with CloudWatch
If you encounter any errors during testing:

1. **Access Lambda Function**:
   - Go to AWS Console > Lambda
   - Find your function: `VoiceGatewayProcessor-<YOUR_REGION>` (e.g., `VoiceGatewayProcessor-us-east-1`)

2. **View Logs**:
   - Click the "Monitor" tab
   - Select "View logs in CloudWatch"
   

3. **Analyze Logs**:
   - Examine the latest log streams
   - Look for error messages or stack traces
   - Common issues include:
     - Invalid API keys
     - Incorrect IAM permissions
     - Unsupported audio formats
     - Service timeouts
## Cleanup

To avoid incurring ongoing AWS charges, delete the entire CloudFormation stack when finished:

1. **Go to CloudFormation**:
   - Navigate to the [AWS CloudFormation console](https://console.aws.amazon.com/cloudformation)

2. **Select Your Stack**:
   - Select your stack (e.g., `FarmAssistVoiceGatewayStack` or your custom name)

3. **Delete Stack**:
   - Click the **"Delete"** button in the top menu

4. **Confirm Deletion**:
   - Check the confirmation box when prompted
   - Click **"Delete stack"**

> **Important Note**: The S3 bucket has `DeletionPolicy: Retain` to prevent accidental data loss.  
> **You must manually delete the S3 bucket**:
> 1. Go to [S3 Console](https://s3.console.aws.amazon.com/)
> 2. Locate your bucket (named similar to `farm-assist-audio-<account-id>-<region>`)
> 3. First **empty** the bucket:
>    - Select bucket > "Empty"
>    - Confirm by typing "permanently delete"
> 4. Then **delete** the bucket:
>    - Select bucket > "Delete"
>    - Enter bucket name to confirm
