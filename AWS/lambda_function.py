import json
import base64
import os
import boto3
import uuid
from botocore.exceptions import ClientError
import time
from urllib.request import Request, urlopen
import requests
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from openai import OpenAI
from dotenv import load_dotenv
import redis
import hashlib

import marketplace_tools

load_dotenv()

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
translate_client = boto3.client('translate')
polly_client = boto3.client('polly')

# Initialize Redis client
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

redis_client = redis.Redis(
    host=REDIS_ENDPOINT,
    port=REDIS_PORT,
    password=REDIS_PASSWORD if REDIS_PASSWORD else None,
    decode_responses=True,
    socket_timeout=2,
    socket_connect_timeout=1
)

# Initialize Gemini client
client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'farmassist-voice-gateway-audio')
TARGET_LLM_LANGUAGE = 'en'
DEFAULT_FARMER_LANGUAGE = 'hi-IN'
CACHE_TTL = int(os.getenv("CACHE_TTL", 3600))  # Default 1 hour

def get_cache_key(query: str, language: str) -> str:
    """Generate consistent cache key from query and language"""
    normalized_query = query.strip().lower()
    return f"llm:{hashlib.sha256(f"{language}:{normalized_query}".encode()).hexdigest()}"

def get_cached_response(query: str, language: str) -> str:
    """Check Redis for cached response"""
    key = get_cache_key(query, language)
    try:
        if cached := redis_client.get(key):
            print(f"⚡ Cache hit for query: {query[:50]}...")
            return cached
    except Exception as e:
        print(f"Redis error (non-fatal): {str(e)}")
    return None

def cache_response(query: str, language: str, response: str, ttl: int = CACHE_TTL):
    """Store response in Redis with expiration"""
    key = get_cache_key(query, language)
    try:
        redis_client.setex(key, ttl, response)
        print(f"Cached response for query: {query[:50]}... (TTL: {ttl}s)")
    except Exception as e:
        print(f"Redis cache write failed (non-fatal): {str(e)}")

def process_tool_calls(response):
    """Process tool calls if needed (existing function)"""
    # Your existing implementation
    pass

def lambda_handler(event, context):
    print(json.dumps(event, indent=2))
    print("Event Body")
    print(event.get('body', 'Body key not found or is None'))
    
    try:
        # 1. Receive Voice Input
        body = json.loads(event['body'])
        audio_base64 = body.get('audio_data')
        farmer_language_code = body.get('farmer_language_code', DEFAULT_FARMER_LANGUAGE)

        if not audio_base64:
            print("Error: Missing audio_data in request body.")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing audio_data in request body'})
            }

        audio_bytes = base64.b64decode(audio_base64)
        unique_id = str(uuid.uuid4())
        input_audio_key = f'input/{unique_id}.wav'

        # 2. Store Audio in S3
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=input_audio_key, Body=audio_bytes)
        audio_s3_uri = f's3://{S3_BUCKET_NAME}/{input_audio_key}'
        print(f"Audio uploaded to S3: {audio_s3_uri}")

        # 3. Convert Voice to Text
        transcription_job_name = f'voice-to-text-{unique_id}'
        transcribe_client.start_transcription_job(
            TranscriptionJobName=transcription_job_name,
            LanguageCode=farmer_language_code,
            MediaFormat='mp3',
            Media={'MediaFileUri': audio_s3_uri},
            OutputBucketName=S3_BUCKET_NAME,
            OutputKey=f'transcripts/{transcription_job_name}.json'
        )

        # Poll for transcription completion
        print("Waiting for transcription job to complete...")
        while True:
            job_status = transcribe_client.get_transcription_job(TranscriptionJobName=transcription_job_name)
            status = job_status['TranscriptionJob']['TranscriptionJobStatus']
            print(f"Transcription job status: {status}")
            if status == 'COMPLETED':
                break
            elif status == 'FAILED':
                raise Exception(f"Transcription job failed: {job_status['TranscriptionJob']['FailureReason']}")
            time.sleep(3)

        # Retrieve transcribed text
        transcript_s3_key = f'transcripts/{transcription_job_name}.json'
        transcript_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
        transcript_content = json.loads(transcript_response['Body'].read().decode('utf-8'))
        transcribed_text = transcript_content['results']['transcripts'][0]['transcript']
        print(f"Transcribed Text: {transcribed_text}")

        # 4. Translate if needed
        text_for_llm = transcribed_text
        if farmer_language_code != TARGET_LLM_LANGUAGE:
            print(f"Translating from {farmer_language_code} to {TARGET_LLM_LANGUAGE}...")
            translate_response = translate_client.translate_text(
                Text=transcribed_text,
                SourceLanguageCode=farmer_language_code,
                TargetLanguageCode=TARGET_LLM_LANGUAGE
            )
            text_for_llm = translate_response['TranslatedText']
            print(f"Translated Text for LLM: {text_for_llm}")

        # 5. Generate Response with LLM (with caching)
        llm_response_text = ""
        try:
            # Check cache first
            cached_response = get_cached_response(text_for_llm, farmer_language_code)
            if cached_response:
                llm_response_text = cached_response
            else:
                llm_prompt = f"You are an agricultural assistant. Based on the following farmer's query, provide a concise and helpful response (max 3 sentences): '{text_for_llm}'"
                
                messages = [{"role": "user", "content": llm_prompt}]
                
                print("Calling Gemini API...")
                response = client.chat.completions.create(
                    model="gemini-2.0-flash",
                    messages=messages,
                    tools=marketplace_tools.tools,
                    tool_choice="auto"
                )
                
                if not process_tool_calls(response):
                    llm_response_text = response.choices[0].message.content
                    # Cache new responses
                    cache_response(text_for_llm, farmer_language_code, llm_response_text)
                else:
                    llm_response_text = "task completed"
                    
            print(f"LLM Response: {llm_response_text}")

        except ValueError as ve:
            print(f"Configuration Error: {ve}")
            llm_response_text = "Configuration error for AI service. Please check API key."
        except Exception as e:
            print(f"Error interacting with LLM: {e}")
            llm_response_text = "I'm sorry, I could not generate an AI response at this time. Please try again."

        # 6. Translate response back if needed
        final_response_text = llm_response_text
        if farmer_language_code != TARGET_LLM_LANGUAGE:
            print(f"Translating response from {TARGET_LLM_LANGUAGE} to {farmer_language_code}...")
            translate_response = translate_client.translate_text(
                Text=llm_response_text,
                SourceLanguageCode=TARGET_LLM_LANGUAGE,
                TargetLanguageCode=farmer_language_code
            )
            final_response_text = translate_response['TranslatedText']
            print(f"Translated Response for Farmer: {final_response_text}")

        # 7. Convert to speech
        polly_response = polly_client.synthesize_speech(
            Text=final_response_text,
            OutputFormat='mp3',
            VoiceId='Kajal',
            LanguageCode=farmer_language_code,
            Engine='neural'
        )
        audio_stream = polly_response['AudioStream'].read()

        # 8. Clean up
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=input_audio_key)
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
        print("Cleaned up temporary S3 files.")

        # 9. Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Processing complete',
                'transcribed_text': transcribed_text,
                'llm_response': llm_response_text,
                'final_spoken_text': final_response_text,
                'audio_response_base64': base64.b64encode(audio_stream).decode('utf-8'),
                'cache_status': 'hit' if cached_response else 'miss'
            })
        }

    except ClientError as e:
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An AWS service error occurred: {str(e)}'})
        }
    except Exception as e:
        print(f"General Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An unexpected error occurred: {str(e)}'})
        }
