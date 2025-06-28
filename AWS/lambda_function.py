import json
import base64
import os
import boto3
import uuid
from botocore.exceptions import ClientError
import time
from urllib.request import Request, urlopen

import requests # Used for making HTTP requests
from openai.types.chat import ChatCompletion, ChatCompletionMessage, ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function
from openai import OpenAI
from dotenv import load_dotenv

import marketplace_tools

load_dotenv()

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
translate_client = boto3.client('translate')
polly_client = boto3.client('polly')

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'farmassist-voice-gateway-audio')
TARGET_LLM_LANGUAGE = 'en'
DEFAULT_FARMER_LANGUAGE = 'hi-IN'

def lambda_handler(event, context):
    print(json.dumps(event, indent=2))
    print("Event Body")
    print(event.get('body', 'Body key not found or is None'))
    try:
        # 1. Receive Voice Input
        # Example JSON payload
        # {
        #   "audio_data": "BASE64_ENCODED_AUDIO_STRING_HERE",
        #   "farmer_language_code": "hi"
        # }

        # API Gateway will parse the JSON body into event['body']
        body = json.loads(event['body'])
        audio_base64 = body.get('audio_data')
        # Get the farmer's language from the request, or use a default
        farmer_language_code = body.get('farmer_language_code', DEFAULT_FARMER_LANGUAGE)

        if not audio_base64:
            print("Error: Missing audio_data in request body.")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing audio_data in request body'})
            }

        audio_bytes = base64.b64decode(audio_base64)
        unique_id = str(uuid.uuid4()) # Generate a unique ID for this transaction
        input_audio_key = f'input/{unique_id}.wav'

        # 2. Store Audio in S3 (for Amazon Transcribe)
        s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=input_audio_key, Body=audio_bytes)
        audio_s3_uri = f's3://{S3_BUCKET_NAME}/{input_audio_key}'
        print(f"Audio uploaded to S3: {audio_s3_uri}")

        # 3. Convert Voice to Text (Amazon Transcribe)
        transcription_job_name = f'voice-to-text-{unique_id}'
        transcribe_client.start_transcription_job(
            TranscriptionJobName=transcription_job_name,
            LanguageCode=farmer_language_code,
            MediaFormat='mp3',
            Media={'MediaFileUri': audio_s3_uri},
            OutputBucketName=S3_BUCKET_NAME,
            OutputKey=f'transcripts/{transcription_job_name}.json'
        )

        # Polling for transcription job completion.
        print("Waiting for transcription job to complete...")
        while True:
            job_status = transcribe_client.get_transcription_job(TranscriptionJobName=transcription_job_name)
            status = job_status['TranscriptionJob']['TranscriptionJobStatus']
            print(f"Transcription job status: {status}")
            if status == 'COMPLETED':
                break
            elif status == 'FAILED':
                raise Exception(f"Transcription job failed: {job_status['TranscriptionJob']['FailureReason']}")
            time.sleep(3) # Wait 3 seconds before checking again

        # Retrieve the transcribed text from S3
        transcript_s3_key = f'transcripts/{transcription_job_name}.json'
        transcript_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
        transcript_content = json.loads(transcript_response['Body'].read().decode('utf-8'))
        transcribed_text = transcript_content['results']['transcripts'][0]['transcript']
        print(f"Transcribed Text: {transcribed_text}")

        # 4. Translate Transcribed Text (if needed)
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
        else:
            print(f"No translation needed. Farmer language ({farmer_language_code}) matches LLM language ({TARGET_LLM_LANGUAGE}).")

        # 5. Generate Response with LLM
        llm_response_text = ""
        try:
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
            else:
                llm_response_text = "task completed"

            print(f"LLM Raw Response: {llm_response_text}")

        except ValueError as ve:
            print(f"Configuration Error: {ve}")
            llm_response_text = "Configuration error for AI service. Please check API key."
        except Exception as e:
            print(f"Error interacting with LLM: {e}")
            llm_response_text = "I'm sorry, I could not generate an AI response at this time. Please try again."

        # 6. Translate LLM Response Back to Farmer's Language (if needed)
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
        else:
            print(f"No translation needed for response. Farmer language ({farmer_language_code}) matches LLM language ({TARGET_LLM_LANGUAGE}).")

        # 7. Convert Text to Speech (Amazon Polly)
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

        # 9. Return Synthesized Audio
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
                'audio_response_base64': base64.b64encode(audio_stream).decode('utf-8')
            })
        }

    except ClientError as e:
        # Handle AWS service-specific errors
        print(f"AWS Client Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An AWS service error occurred: {str(e)}'})
        }
    except Exception as e:
        # Catch any other unexpected errors
        print(f"General Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'An unexpected error occurred: {str(e)}'})
        }
