# Voice Processing Gateway for Agricultural Assistance

This AWS Lambda function processes voice inputs from farmers, generates AI responses using Gemini, and returns audio responses. The system handles multilingual conversations using AWS Transcribe, Translate, and Polly services.

## Demo Video
https://github.com/user-attachments/assets/17e0aef0-bae6-435f-b930-706cfd088f27

## Process
<img src="https://github.com/user-attachments/assets/5c39c36b-e3a8-4c67-8f65-d6130d45ee48" alt="logic flow" height="2160">

## AWS Services Used

- **AWS CloudFormation**: For Infrastructure as Code (IaC), allowing declarative provisioning and management of all AWS resources.
- **AWS Lambda**: Serverless compute for the core application logic.
- **Amazon API Gateway**: A fully managed service to create, publish, maintain, monitor, and secure APIs.
- **Amazon S3**: Scalable object storage for audio and transcription data.
- **Amazon Transcribe**: Automated speech recognition (ASR) service.
- **Amazon Translate**: Neural machine translation service.
- **Amazon Polly**: Text-to-Speech (TTS) service with natural-sounding voices.
- **AWS IAM**: Manages access and permissions across AWS services.
- **Amazon CloudWatch**: For logging and monitoring.

### Response Caching Mechanism

This project incorporates a caching mechanism using Redis to store query responses, improving performance and reducing the load on external services.

-   **`cache.py`**: This file defines the `RedisCache` class, which encapsulates the logic for interacting with a Redis server. It provides methods for:
    * Generating a unique SHA256 hash for a given query to use as a cache key.
    * Retrieving a cached response based on a query.
    * Storing a query-response pair in the cache, with an optional time-to-live (TTL) for expiration. Environment variables (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`) are used for Redis connection details.

-   **`add_cache.py`**: This script is a command-line utility for manually adding entries to the Redis cache.
    * **Usage**: `python add_cache.py <query> <response> [ttl_in_seconds]`
    * `<query>`: The query string to be used as the cache key.
    * `<response>`: The response string to be cached.
    * `[ttl_in_seconds]`: (Optional) The time-to-live for the cache entry in seconds. If set to `0` or `None`, the entry will be permanent.
    * Example:
      - 1 hour cache: ```python3 add_cache.py "What is the capital of Canada?" "Ottawa" 3600```
      - Permanent cache: ```python3 add_cache.py "What is the capital of Canada?" "Ottawa"```
    * This script utilizes the `RedisCache` class from `cache.py` to perform the caching operation.

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

### How to Run Test Script (`AWS/Test/test.py`)

### Update Placeholders
1. In `test.py`:
   - Replace `YOUR_API_GATEWAY_INVOKE_URL_HERE` with your actual API Gateway URL
   - Replace `path/to/your/test_audio.mp3` with your audio file path

### Execute the Script
```bash
python test.py
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
