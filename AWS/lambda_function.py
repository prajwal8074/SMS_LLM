import json
import base64
import os
import boto3
import uuid
from botocore.exceptions import ClientError
import time
from urllib.request import Request, urlopen, HTTPError

# Initialize AWS clients
s3_client = boto3.client('s3')
transcribe_client = boto3.client('transcribe')
translate_client = boto3.client('translate')
polly_client = boto3.client('polly')

# --- Configuration ---
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'farmassist-voice-gateway-audio')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

# Target language for Large Language Model (LLM) processing
TARGET_LLM_LANGUAGE = 'en'
# Default language for farmer's input and Polly output, used as a fallback.
DEFAULT_FARMER_LANGUAGE = 'hi-IN'

# List of languages Amazon Transcribe should attempt to identify.
# Ensure these are full BCP-47 codes as per AWS Transcribe documentation.
SUPPORTED_TRANSCRIBE_LANGUAGES = [
    'en-US', # English (United States)
    'hi-IN', # Hindi (India)
    'gu-IN', # Gujarati (India)
    'mr-IN', # Marathi (India)
    'bn-IN', # Bengali (India)
    'ta-IN', # Tamil (India)
    'te-IN', # Telugu (India)
    'kn-IN', # Kannada (India)
    'ml-IN', # Malayalam (India)
    'pa-IN', # Punjabi (India)
]

# Languages supported by Polly's describe_voices API for direct voice lookup.
# Some Indian languages supported for synthesis may not appear in this list for lookup.
POLLY_DESCRIBE_VOICES_SUPPORTED_LANGUAGES = [
    'en-IE', 'ar-AE', 'en-US', 'fr-BE', 'en-IN', 'es-MX', 'en-ZA', 'tr-TR', 'ru-RU',
    'ro-RO', 'pt-PT', 'pl-PL', 'nl-NL', 'it-IT', 'is-IS', 'fr-FR', 'fi-FI', 'es-ES',
    'de-DE', 'yue-CN', 'ko-KR', 'en-NZ', 'en-GB-WLS', 'hi-IN', 'de-CH', 'arb',
    'nl-BE', 'cy-GB', 'cs-CZ', 'cmn-CN', 'da-DK', 'en-AU', 'pt-BR', 'nb-NO',
    'sv-SE', 'ja-JP', 'es-US', 'ca-ES', 'fr-CA', 'en-GB', 'de-AT',
]

# Global function to ensure consistent logging and handle encoding issues.
def safe_print(message, *args, **kwargs):
    try:
        print(message, *args, **kwargs)
    except UnicodeEncodeError:
        try:
            print(str(message).encode('utf-8', errors='replace').decode('utf-8'), *args, **kwargs)
        except Exception as e_inner:
            print(f"Error printing message (fallback failed): {e_inner}")
            print("Original message (truncated):", str(message)[:200])


def lambda_handler(event, context):
    http_method = event.get('httpMethod')

    # --- Webhook Verification Logic for GET requests ---
    if http_method == 'GET':
        safe_print("Received GET request for webhook verification.")
        query_params = event.get('queryStringParameters', {})
        mode = query_params.get('hub.mode')
        token = query_params.get('hub.verify_token')
        challenge = query_params.get('hub.challenge')

        # FB_VERIFY_TOKEN is not used in this simplified version, but keeping the structure
        # if it was part of a previous integration. For a generic voice gateway,
        # you might simply return the challenge if mode is 'subscribe'.
        if mode == 'subscribe' and challenge:
            safe_print(f"Webhook verification successful. Returning challenge: {challenge}")
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'text/plain'
                },
                'body': challenge
            }
        else:
            safe_print("Webhook verification failed: Invalid mode or token.")
            return {
                'statusCode': 403,
                'body': 'Verification failed'
            }

    # --- Main Voice Processing Logic for POST requests ---
    elif http_method == 'POST':
        safe_print("Received POST request for voice processing.")
        body_data = {}
        audio_filename = ""
        transcription_job_name = ""
        transcript_s3_key = ""
        detected_language = ""

        try:
            raw_body_from_event = event.get('body', None)
            if raw_body_from_event:
                if event.get('isBase64Encoded', False):
                    decoded_string = base64.b64decode(raw_body_from_event).decode('utf-8')
                else:
                    decoded_string = raw_body_from_event
                body_data = json.loads(decoded_string)
            else:
                raise ValueError("Received empty or None body from API Gateway.")

        except json.JSONDecodeError as e:
            safe_print(f"JSON Decode Failed: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'Failed to parse JSON body after decode: {str(e)}'})
            }
        except UnicodeDecodeError as e:
            safe_print(f"Unicode Decode Failed: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'Failed to decode Base64 to UTF-8: {str(e)}'})
            }
        except Exception as e:
            safe_print(f"Unexpected exception during body processing: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'An unexpected error occurred during body parsing: {str(e)}'})
            }

        audio_base64 = body_data.get('audio_data')
        if not audio_base64:
            safe_print("Validation Error: Missing audio_data in request body.")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Missing audio_data in request body'})
            }

        # --- 2. Upload Audio to S3 ---
        try:
            audio_bytes = base64.b64decode(audio_base64)
            unique_id = str(uuid.uuid4())
            audio_filename = f"incoming_audio/{unique_id}.mp3"
            s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=audio_filename, Body=audio_bytes)
            audio_s3_uri = f"s3://{S3_BUCKET_NAME}/{audio_filename}"
            safe_print(f"Audio uploaded to S3: {audio_s3_uri}")
        except ClientError as e:
            safe_print(f"S3 Upload Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'Failed to upload audio to S3: {str(e)}'})
            }

        # --- 3. Convert Voice to Text using Amazon Transcribe ---
        transcription_job_name = f'voice-to-text-{unique_id}'
        transcribed_text = ""
        transcript_s3_key = f'transcripts/{transcription_job_name}.json'

        try:
            safe_print(f"Starting transcribe job with language identification from: {SUPPORTED_TRANSCRIBE_LANGUAGES}")
            transcribe_client.start_transcription_job(
                TranscriptionJobName=transcription_job_name,
                IdentifyLanguage=True,
                LanguageOptions=SUPPORTED_TRANSCRIBE_LANGUAGES,
                MediaFormat='mp3',
                Media={'MediaFileUri': audio_s3_uri},
                OutputBucketName=S3_BUCKET_NAME,
                OutputKey=transcript_s3_key
            )
            safe_print(f"Transcribe job started: {transcription_job_name}")

            # Polling for transcription job completion
            safe_print("Waiting for transcription job to complete...")
            max_attempts = 120 # 10 minutes timeout
            for i in range(max_attempts):
                job_status = transcribe_client.get_transcription_job(TranscriptionJobName=transcription_job_name)
                status = job_status['TranscriptionJob']['TranscriptionJobStatus']
                safe_print(f"Transcription job status: {status}. Waiting... ({i+1}/{max_attempts})")

                if status == 'COMPLETED':
                    safe_print("Transcription job completed successfully.")
                    detected_language = job_status['TranscriptionJob'].get('LanguageCode', DEFAULT_FARMER_LANGUAGE)
                    safe_print(f"Detected Language: {detected_language}")

                    try:
                        safe_print(f"Attempting to fetch transcript from S3 Key: {transcript_s3_key}")
                        transcript_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
                        transcript_content = json.loads(transcript_response['Body'].read().decode('utf-8'))
                        transcribed_text = transcript_content['results']['transcripts'][0]['transcript']
                        transcribed_text = transcribed_text.encode('utf-8', errors='replace').decode('utf-8')
                        safe_print(f"Transcribed Text: {transcribed_text}")
                        break
                    except ClientError as s3_e:
                        safe_print(f"S3 GetObject Error: {s3_e}")
                        raise Exception(f"Failed to fetch transcript from S3: {str(s3_e)}")
                    except Exception as inner_e:
                        safe_print(f"Error processing transcript content: {inner_e}")
                        raise Exception(f"Failed to process transcript content: {str(inner_e)}")

                elif status == 'FAILED':
                    failure_reason = job_status['TranscriptionJob'].get('FailureReason', 'Unknown reason')
                    safe_print(f"Transcription job failed: {failure_reason}")
                    raise Exception(f"Transcription failed: {failure_reason}")
                time.sleep(5)
            else:
                raise Exception("Transcription job timed out.")

        except Exception as e:
            safe_print(f"Transcribe Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'An AWS service error occurred during transcription: {str(e)}'})
            }

        # --- 4. Translate Transcribed Text for LLM if necessary ---
        text_for_llm = transcribed_text
        source_language_for_translate = detected_language if detected_language else DEFAULT_FARMER_LANGUAGE.split('-')[0]

        if source_language_for_translate != TARGET_LLM_LANGUAGE:
            safe_print(f"Translating from {source_language_for_translate} to {TARGET_LLM_LANGUAGE} for LLM.")
            try:
                translate_response = translate_client.translate_text(
                    Text=transcribed_text,
                    SourceLanguageCode=source_language_for_translate,
                    TargetLanguageCode=TARGET_LLM_LANGUAGE
                )
                text_for_llm = translate_response['TranslatedText']
                text_for_llm = text_for_llm.encode('utf-8', errors='replace').decode('utf-8')
                safe_print(f"Translated Text for LLM: {text_for_llm}")
            except ClientError as e:
                safe_print(f"Translate Error during LLM input translation: {e}")
                text_for_llm = transcribed_text # Continue with original text if translation fails
                safe_print("Translation for LLM input failed, proceeding with original transcribed text.")
        else:
            safe_print(f"No translation needed for LLM input. Farmer language ({source_language_for_translate}) matches LLM target language ({TARGET_LLM_LANGUAGE}).")

        # --- 5. Generate Response with LLM (Gemini API) ---
        llm_response_text = ""
        try:
            gemini_api_key = os.environ.get('GEMINI_API_KEY')
            if not gemini_api_key:
                raise ValueError("GEMINI_API_KEY environment variable is not set.")

            llm_prompt = (
                f"You are an agricultural assistant. Based on the following farmer's query, provide a concise and helpful response (max 3 sentences): '{text_for_llm}'. "
                f"Ensure the response is relevant to agricultural advice. Respond in the same language as the query, which is {TARGET_LLM_LANGUAGE}."
            )
            chat_history = [{'role': 'user', 'parts': [{'text': llm_prompt}]}]
            payload = {'contents': chat_history}
            headers = {'Content-Type': 'application/json'}
            gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"

            req = Request(
                gemini_api_url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )

            safe_print("Calling Gemini API...")
            with urlopen(req, timeout=30) as res:
                llm_result = json.loads(res.read().decode('utf-8'))
                if llm_result and 'candidates' in llm_result and len(llm_result['candidates']) > 0 and \
                   'content' in llm_result['candidates'][0] and 'parts' in llm_result['candidates'][0]['content'] and \
                   len(llm_result['candidates'][0]['content']['parts']) > 0:
                    llm_response_text = llm_result['candidates'][0]['content']['parts'][0]['text']
                    llm_response_text = llm_response_text.encode('utf-8', errors='replace').decode('utf-8')
                else:
                    llm_response_text = "I'm sorry, the AI did not provide a valid response."
                    safe_print(f"Warning: Invalid Gemini API response structure: {llm_result}")

            safe_print(f"LLM Raw Response: {llm_response_text}")

        except HTTPError as http_e:
            error_body = http_e.read().decode('utf-8')
            safe_print(f"HTTPError calling Gemini API: Status {http_e.code}, Reason: {http_e.reason}, Body: {error_body}")
            llm_response_text = f"I'm sorry, I couldn't get a response from the AI assistant due to an external service error (HTTP {http_e.code})."
        except ValueError as ve:
            safe_print(f"Configuration Error (Gemini): {ve}")
            llm_response_text = "Configuration error for AI service. Please check API key."
        except Exception as e:
            safe_print(f"Error interacting with LLM: {e}")
            llm_response_text = "I'm sorry, I could not generate an AI response at this time. Please try again."

        # --- 6. Translate LLM Response Back to Farmer's Language for Polly ---
        final_response_text = llm_response_text
        polly_desired_output_language_code = detected_language if detected_language else DEFAULT_FARMER_LANGUAGE

        # Translate to Hindi if detected Indian language is not directly supported by Polly's describe_voices
        target_language_for_polly_translation = polly_desired_output_language_code
        if polly_desired_output_language_code.startswith(('gu-IN', 'mr-IN', 'bn-IN', 'ta-IN', 'te-IN', 'kn-IN', 'ml-IN', 'pa-IN')):
            safe_print(f"Detected Indian language '{polly_desired_output_language_code}' will be translated to Hindi ('hi-IN') for Polly synthesis.")
            target_language_for_polly_translation = 'hi-IN'

        if target_language_for_polly_translation.split('-')[0] != TARGET_LLM_LANGUAGE:
            safe_print(f"Translating response from {TARGET_LLM_LANGUAGE} to {target_language_for_polly_translation} for Polly.")
            try:
                translate_response = translate_client.translate_text(
                    Text=llm_response_text,
                    SourceLanguageCode=TARGET_LLM_LANGUAGE,
                    TargetLanguageCode=target_language_for_polly_translation
                )
                final_response_text = translate_response['TranslatedText']
                final_response_text = final_response_text.encode('utf-8', errors='replace').decode('utf-8')
                safe_print(f"Translated Response for Farmer: {final_response_text}")
            except ClientError as e:
                safe_print(f"Translate Error during TTS output translation: {e}")
                # Fallback translation if the first attempt fails
                try:
                    safe_print(f"Attempting fallback translation to {DEFAULT_FARMER_LANGUAGE}.")
                    fallback_translate_response = translate_client.translate_text(
                        Text=llm_response_text,
                        SourceLanguageCode=TARGET_LLM_LANGUAGE,
                        TargetLanguageCode=DEFAULT_FARMER_LANGUAGE
                    )
                    final_response_text = fallback_translate_response['TranslatedText']
                    final_response_text = final_response_text.encode('utf-8', errors='replace').decode('utf-8')
                    polly_desired_output_language_code = DEFAULT_FARMER_LANGUAGE
                    safe_print(f"Translated to fallback language {DEFAULT_FARMER_LANGUAGE} for TTS.")
                except ClientError as e_fallback:
                    safe_print(f"Fallback translation to {DEFAULT_FARMER_LANGUAGE} also failed: {e_fallback}")
                    final_response_text = llm_response_text # Revert to English LLM response
                    polly_desired_output_language_code = TARGET_LLM_LANGUAGE # Use English for Polly synthesis
                    safe_print("All translation attempts failed. Proceeding with LLM's raw English response for TTS.")
                safe_print("Translation for TTS output failed, proceeding with LLM's raw response (possibly translated to fallback).")
        else:
            safe_print(f"No translation needed for response. Detected language ({polly_desired_output_language_code}) matches LLM target language ({TARGET_LLM_LANGUAGE}).")

        # --- 7. Convert Text to Speech using Amazon Polly ---
        audio_stream = None
        polly_voice_id = None
        polly_engine = 'standard'
        actual_synthesis_language_code = polly_desired_output_language_code

        try:
            # Voice selection logic based on language and availability
            if actual_synthesis_language_code == 'hi-IN':
                polly_voice_id = 'Kajal'
                polly_engine = 'neural'
                safe_print(f"Using Hindi voice: {polly_voice_id}")
            elif actual_synthesis_language_code == 'en-IN':
                polly_voice_id = 'Aditi'
                polly_engine = 'neural'
                safe_print(f"Using English-Indian voice: {polly_voice_id}")
            elif actual_synthesis_language_code in ['gu-IN', 'mr-IN', 'bn-IN', 'ta-IN', 'te-IN', 'kn-IN', 'ml-IN', 'pa-IN'] and target_language_for_polly_translation == 'hi-IN':
                polly_voice_id = 'Kajal'
                polly_engine = 'neural'
                actual_synthesis_language_code = 'hi-IN' # Ensure language code for synthesis is 'hi-IN'
                safe_print(f"Synthesizing detected Indian language via Hindi (Kajal) fallback.")
            elif actual_synthesis_language_code in POLLY_DESCRIBE_VOICES_SUPPORTED_LANGUAGES:
                polly_voices_response_neural = polly_client.describe_voices(
                    LanguageCode=actual_synthesis_language_code, Engine='neural'
                )
                if polly_voices_response_neural and 'Voices' in polly_voices_response_neural and len(polly_voices_response_neural['Voices']) > 0:
                    polly_voice_id = polly_voices_response_neural['Voices'][0]['Id']
                    polly_engine = 'neural'
                    safe_print(f"Found Polly neural voice '{polly_voice_id}' for '{actual_synthesis_language_code}'.")
                else:
                    polly_voices_response_standard = polly_client.describe_voices(
                        LanguageCode=actual_synthesis_language_code, Engine='standard'
                    )
                    if polly_voices_response_standard and 'Voices' in polly_voices_response_standard and len(polly_voices_response_standard['Voices']) > 0:
                        polly_voice_id = polly_voices_response_standard['Voices'][0]['Id']
                        polly_engine = 'standard'
                        safe_print(f"Found Polly standard voice '{polly_voice_id}' for '{actual_synthesis_language_code}'.")
            
            if not polly_voice_id:
                safe_print(f"No suitable Polly voice found for '{actual_synthesis_language_code}'. Falling back to default English (Joanna).")
                polly_voice_id = 'Joanna'
                actual_synthesis_language_code = 'en-US'
                polly_engine = 'neural'

            if not polly_voice_id:
                raise Exception("Could not determine a Polly VoiceId for speech synthesis after all fallback attempts.")

            polly_response = polly_client.synthesize_speech(
                Text=final_response_text,
                OutputFormat='mp3',
                VoiceId=polly_voice_id,
                LanguageCode=actual_synthesis_language_code,
                Engine=polly_engine
            )
            audio_stream = polly_response['AudioStream'].read()
            safe_print("Speech synthesized with Polly.")

        except ClientError as e:
            safe_print(f"Polly Synthesis Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'An AWS service error occurred during speech synthesis (Polly): {str(e)}'})
            }
        except Exception as e:
            safe_print(f"General TTS Error: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'message': f'An unexpected error occurred during speech synthesis: {str(e)}'})
            }

        # --- 8. Clean up temporary S3 files ---
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=audio_filename)
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
            safe_print("Cleaned up temporary S3 files.")
        except ClientError as e:
            safe_print(f"Warning: Failed to cleanup S3 objects: {e}")
        except Exception as e:
            safe_print(f"General cleanup warning: {e}")

        # --- 9. Return Synthesized Audio Response ---
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # Required for CORS
            },
            'body': json.dumps({
                'message': 'Processing complete',
                'transcribed_text': transcribed_text,
                'llm_response': llm_response_text,
                'final_spoken_text': final_response_text,
                'audio_response_base64': base64.b64encode(audio_stream).decode('utf-8') if audio_stream else None,
                'detected_language': detected_language
            })
        }

    else:
        safe_print(f"Unsupported HTTP method: {http_method}")
        return {
            'statusCode': 405,
            'body': json.dumps({'message': 'Method Not Allowed'})
        }
