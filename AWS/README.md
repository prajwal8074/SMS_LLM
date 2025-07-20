# Voice Processing Gateway for Agricultural Assistance

This AWS Lambda function processes voice inputs from farmers, generates AI responses using Gemini, and returns audio responses. The system handles multilingual conversations using AWS Transcribe, Translate, and Polly services.

## Demo Video
https://github.com/user-attachments/assets/17e0aef0-bae6-435f-b930-706cfd088f27

## Response Caching Demo
   - Semantic Caching: The application uses a sophisticated caching system with Redis and Sentence Transformers to cache responses based on the meaning of a query, not just the exact text. This can significantly improve performance and reduce redundant processing.
   - Cache Management: The add_cache.py script provides a way to manually add entries to the cache.
   - <img width="1920" height="1080" alt="Screenshot from 2025-07-19 05-11-36" src="https://github.com/user-attachments/assets/b8bed692-dce5-4ac0-bb6e-99241dbbfc10" />

## Process
<img src="https://github.com/user-attachments/assets/5c39c36b-e3a8-4c67-8f65-d6130d45ee48" alt="logic flow" height="2160">

## AWS Services Used

- **AWS CloudFormation**: For Infrastructure as Code (IaC), allowing declarative provisioning and management of all AWS resources.
- **Amazon S3**: Scalable object storage for audio and transcription data.
- **Amazon Transcribe**: Automated speech recognition (ASR) service.
- **Amazon Translate**: Neural machine translation service.
- **Amazon Polly**: Text-to-Speech (TTS) service with natural-sounding voices.
- **AWS IAM**: Manages access and permissions across AWS services.
- **Amazon CloudWatch**: For logging and monitoring.
- **Amazon EC2**: For Deployment.

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
### Check the workflow .github/workflows/deploy.yml for better understanding
### Also check the workflow aws-unit-tests.yml.yml for understanding project features

## Table of Contents
- [System Architecture Overview](#1-system-architecture-overview)
- [Prerequisites](#2-prerequisites)
- [EC2 Instance Setup](#3-ec2-instance-setup)
- [AWS IAM Role Configuration](#4-aws-iam-role-configuration)
- [Application Deployment on EC2](#5-application-deployment-on-ec2)
- [Running the Flask Application](#6-running-the-flask-application)
- [Testing the Gateway](#7-testing-the-gateway)
- [Security Considerations](#8-security-considerations)
- [Troubleshooting Common Issues](#9-troubleshooting-common-issues)
- [Cleanup](#10-cleanup)

## 1. System Architecture Overview
The FarmAssist Voice Gateway, when deployed on an EC2 instance, acts as a unified backend for voice processing and marketplace interactions. It leverages several AWS services and external APIs:

* **Client Interaction**: Farmers send voice input (via a client application) to the EC2 instance's public API endpoint
* **EC2 Instance (Flask Application)**: Hosts the main Python Flask application (`app.py`) which integrates the voice processing logic
* **AWS SDK (Boto3)**: Interacts with AWS services (S3, Transcribe, Translate, Polly)
* **Google Gemini API**: Provides the Large Language Model for natural language understanding
* **Firebase Admin SDK**: Manages farmer authentication and interacts with Firestore
* **Redis (Caching)**: Used for caching LLM responses and conversation context
* **Marketplace Tools**: Python modules (`marketplace_tools.py`) for business logic
* **Amazon S3**: Stores temporary audio files for transcription
* **Amazon Transcribe**: Converts spoken audio into text
* **Amazon Translate**: Translates text between languages
* **Amazon Polly**: Converts text responses into speech
* **Firebase (Authentication & Firestore)**:
  - Authentication: Manages farmer user accounts
  - Firestore: Stores marketplace item listings
* **Redis Server**: Provides in-memory data structure store

**Flow**:  
`Voice Input -> EC2 Flask App -> (S3, Transcribe, Translate, Gemini, Redis, Firebase/Firestore) -> EC2 Flask App -> Spoken Audio Output`

## 2. Prerequisites
Before you begin, ensure you have:

* An active AWS Account with sufficient permissions
* A Google Cloud Project or Google AI Studio account for Gemini API Key
* A Firebase Project with Authentication and Firestore enabled
* PuTTY (for Windows) or SSH client (for macOS/Linux)
* Your EC2 Key Pair (.pem file) downloaded and secured
* Git installed on your local machine and EC2 instance

## 3. EC2 Instance Setup
Follow these steps to launch and configure your EC2 instance.

### 3.1. Launch EC2 Instance
1. Log in to AWS Management Console
2. Navigate to EC2 (under Services -> Compute)
3. Click "Launch instance"
4. **Choose AMI**: Select Ubuntu Server 22.04 LTS or later
5. **Instance Type**: t2.micro or t3.micro for development
6. **Configure Security Group**:
   - Add Inbound Rules:
     - SSH (Port 22): Source My IP
     - Custom TCP (Port 5002): Source Anywhere-IPv4 (for testing)
7. **Review and Launch**:
   - Select/create key pair
   - Download .pem file
   - Launch instance

### 3.2. Connect to Your EC2 Instance via SSH
#### For macOS/Linux/Git Bash:
```bash
chmod 400 /path/to/your-key-pair.pem
ssh -i /path/to/your-key-pair.pem ubuntu@YOUR_EC2_PUBLIC_IP_OR_DNS
```
## For Windows Users (using PuTTY)

PuTTY requires keys in .ppk format. First, convert your .pem to .ppk using PuTTYgen, then set file permissions.

### Convert .pem to .ppk

1. Open PuTTYgen
2. Click "Load" and select your .pem file
3. Click "Save private key" and save it as a .ppk file (e.g., `my-ec2-key.ppk`)

### Set .ppk file permissions (Crucial for PuTTY)

1. Right-click on your .ppk file and select "Properties"
2. Go to the "Security" tab
3. Click "Advanced"
4. Click "Disable inheritance". If prompted, choose "Convert inherited permissions into explicit permissions on this object."
5. Remove all users/groups from the "Permission entries" list except for your own user account
6. Edit your user's permissions:
   - Select your user
   - Click "Edit"
   - Ensure only "Read" and "Read & execute" are checked under "Allow" permissions
   - Uncheck all others
7. Click "OK" on all dialogs

### Connect with PuTTY

1. Open PuTTY
2. In the "Session" category:
   - Host Name (or IP address): `ubuntu@YOUR_EC2_PUBLIC_IP_OR_DNS`
   - Port: `22`
3. In the "Connection" -> "SSH" -> "Auth" category:
   - Click "Browse..." and select your generated .ppk file
4. Click "Open"
5. Accept the host key if prompted

## 3.3. Set Up Environment

Once connected via SSH:<br>
**Setup ```gh auth login```**

### Update Package Lists
```bash
sudo apt update
```
### Install Python3, pip, and venv
```bash
# For Ubuntu 24.04 and later:
sudo apt install python3 python3-pip python3.12-venv git -y

# For older Ubuntu versions (e.g., 22.04):
sudo apt install python3 python3-pip python3-venv -y
```

## 4. AWS IAM Role Configuration

Your EC2 instance needs an IAM Role with permissions to interact with AWS services like S3, Transcribe, Translate, and Polly.

### Steps to Configure IAM Role:

1. **Go to IAM in AWS Console**
   - Navigate to the IAM service

2. **Create new IAM Role**
   - Choose "AWS service" as trusted entity type
   - Select "EC2" as the service that will use this role
   - Click "Next"

3. **Attach Permission Policies**
   - Add these managed policies:
     * `AmazonS3FullAccess` (or `AmazonS3ReadOnlyAccess` with specific bucket write permissions)
     * `AmazonTranscribeFullAccess`
     * `TranslateFullAccess`
     * `AmazonPollyFullAccess`
     * `CloudWatchLogsFullAccess` (for debugging)
   - Click "Next"

4. **Name the Role**
   - Enter a descriptive name (e.g., `FarmAssistEC2VoiceGatewayRole`)
   - Click "Create role"

5. **Attach Role to EC2 Instance**
   - Go to EC2 Dashboard → Instances
   - Select your running EC2 instance
   - Click "Actions" → "Security" → "Modify IAM role"
   - Select your newly created role
   - Click "Update IAM role"

## 5. Application Deployment on EC2

### 5.1. Application Code Deployment

#### Clone the Repository
```bash
git clone https://github.com/annam-ai-iitropar/team_7B.git ~/farmassist_voice_gateway
```
**Start Containers**

```
docker run -d --name redis-test -p 6379:6379 redis:latest
cd ~/farmassist_voice_gateway/AWS/MarketPlace/backend
sudo docker compose up
```

**you should see all of the below without any additional errors to ensure the containers are fully functional**<br>
The specific output with prefix 'backend-app-1' should look like:
```
[2025-07-20 05:27:06 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2025-07-20 05:27:06 +0000] [1] [INFO] Listening at: http://0.0.0.0:5002 (1)
[2025-07-20 05:27:06 +0000] [1] [INFO] Using worker: sync
[2025-07-20 05:27:06 +0000] [6] [INFO] Booting worker with pid: 6
huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
To disable this warning, you can either:
	- Avoid using `tokenizers` before the fork if possible
	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
FLASK_SERVER_BASE_URL: http://localhost:5002
AWS Boto3 clients initialized for region: us-west-2
REDIS_HOST: redis
RediSearch index 'semantic_cache_idx' created successfully.
```

## 7. Testing the Gateway

Use the provided Python script on your local PC to test your deployed EC2 Flask API.

### 7.1. Local Test Script (`test_gateway.py`)

Create a file named `test_gateway.py` with this content:
<details><summary>test_gateway.py</summary>
   
```python
import requests
import base64
import json
import os
import sys

# --- Configuration ---
API_GATEWAY_URL = "http://YOUR_EC2_PUBLIC_IP:5002/api/process-voice"  # Replace with your EC2 IP
AUDIO_FILE_PATH = "path/to/your/test_audio.mp3"  # Replace with your audio file path
FARMER_LANGUAGE = "hi-IN"  # Language code (e.g., "hi-IN", "en-US")

def safe_local_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        try:
            sys.stdout.buffer.write((str(message) + "\n").encode('utf-8', errors='replace'))
        except Exception as e_inner:
            print(f"Print error (fallback failed): {repr(e_inner)}")
            print("Original message (truncated):", str(message)[:200])

def send_voice_to_gateway(audio_path, lang_code):
    """Send audio to EC2 Flask API and process response."""
    if not os.path.exists(audio_path):
        safe_local_print(f"Error: Audio file not found at {audio_path}")
        return

    try:
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')

        payload = {
            "audio_data": audio_base64,
            "farmer_language_code": lang_code,
            "mobile_number": "+919876543210"  # Test number
        }

        headers = {"Content-Type": "application/json"}

        safe_local_print(f"Sending audio to {API_GATEWAY_URL}...")
        response = requests.post(API_GATEWAY_URL, headers=headers, data=json.dumps(payload))

        if response.status_code == 200:
            result = response.json()
            safe_local_print("\n--- Success ---")
            safe_local_print(f"Message: {result.get('message')}")
            safe_local_print(f"Transcribed Text: {result.get('transcribed_text', 'N/A')}")
            safe_local_print(f"LLM Response: {result.get('llm_response', 'N/A')}")
            safe_local_print(f"Final Spoken Text: {result.get('final_spoken_text', 'N/A')}")
            safe_local_print(f"Detected Language: {result.get('detected_language', 'N/A')}")
            
            if result.get('audio_response_base64'):
                with open("output_response.mp3", "wb") as f:
                    f.write(base64.b64decode(result['audio_response_base64']))
                safe_local_print("Saved AI response as output_response.mp3")

        else:
            safe_local_print(f"\n--- Error ({response.status_code}) ---")
            safe_local_print(response.text.encode('utf-8', errors='replace').decode('utf-8'))

    except Exception as e:
        safe_local_print(f"Error: {repr(e)}")

if __name__ == "__main__":
    send_voice_to_gateway(AUDIO_FILE_PATH, FARMER_LANGUAGE)
```
</details>

## 7.2. Run the Test Script

Follow these steps to test your deployed API:

1. **YOUR_EC2_PUBLIC_IP**  
   Replace YOUR_EC2_PUBLIC_IP with your public ip address assigned to the EC2 instance

2. **Prepare your audio file**  
   Place your test audio file (MP3 or WAV format) in a known location and update the path in the script:
   ```python
   AUDIO_FILE_PATH = "path/to/your/test_audio.mp3"  # Update this path
   ```
1. Save the code: Save the above Python code as test_gateway.py on your local PC.

2. Place your audio file: Ensure your test_audio.mp3 (or whatever your AUDIO_FILE_PATH is set to) is accessible from where you run the script.

3. Install `requests` locally: If you don't have it, open your local terminal/command prompt and run:
```python
pip install requests
```
4. Execute: Run the script from your local terminal:
```python
python test_gateway.py
```
You should see an output similar to the Demo video above.

## 10. Cleanup
To avoid incurring ongoing AWS charges, you can delete the resources when you are finished.

**Terminate EC2 Instance**: Go to the EC2 Dashboard -> Instances. Select your instance, click "Instance state" -> "Terminate instance".

**Delete S3 Bucket**: If you created a dedicated S3 bucket, go to the S3 console, select your bucket, and delete it (after emptying it).

**Delete IAM Role**: If you created a specific IAM role for this EC2 instance, go to IAM -> Roles and delete it.
