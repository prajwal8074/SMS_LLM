# Voice Processing Gateway for Agricultural Assistance

This AWS Lambda function processes voice inputs from farmers, generates AI responses using Gemini, and returns audio responses. The system handles multilingual conversations using AWS Transcribe, Translate, and Polly services.

## Process
![process](https://github.com/user-attachments/assets/5c39c36b-e3a8-4c67-8f65-d6130d45ee48)


## Demo Video
https://github.com/user-attachments/assets/17e0aef0-bae6-435f-b930-706cfd088f27



# How to Reproduce

## Prerequisites
1. **AWS Account** with permissions for:
   - Lambda, S3, Transcribe, Translate, Polly
2. **Gemini API Key** (from Google AI Studio)
3. **Python 3.9+**
4. **Required Packages**:
   ```bash
   pip install boto3 requests
   ```

## Setup Instructions

### 1. Lambda Deployment
1. Create S3 bucket:
   ```bash
   aws s3api create-bucket --bucket farmassist-voice-gateway-audio --region us-west-2
   ```
2. Create Lambda function with Python 3.12 runtime
3. Set environment variables:
   - `S3_BUCKET_NAME`: `farmassist-voice-gateway-audio`
   - `GEMINI_API_KEY`: `your_gemini_key_here`
4. Add IAM execution role with permissions for:
   - S3 (Full access)
   - Transcribe (StartJob, GetJob)
   - Translate (TranslateText)
   - Polly (SynthesizeSpeech)

### 2. API Gateway Configuration
1. Create REST API endpoint
2. Configure POST method to trigger Lambda
3. Enable CORS with headers:
   ```yaml
   Access-Control-Allow-Origin: '*'
   Access-Control-Allow-Methods: 'POST'
   Access-Control-Allow-Headers: 'Content-Type'
   ```

### 3. Test Client Setup (`test.py`)
1. Install dependencies:
   ```bash
   pip install requests
   ```
2. Place audio file `test.mp3` in same directory
3. Configure variables:
   ```python
   API_GATEWAY_URL = "YOUR_API_GATEWAY_ENDPOINT"
   FARMER_LANGUAGE = "hi-IN"
   ```

## Running the Test
```bash
python3 test.py
```

## File Structure
```
AWS/
├── lambda_function.py
└── Test
     ├── test.py
     ├── test.mp3
     └── output_response.mp3
```
