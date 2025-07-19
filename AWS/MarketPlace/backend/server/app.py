from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from database import get_db_connection
import json
import os
import base64
import time
import boto3
import sys
from botocore.exceptions import ClientError
from openai import OpenAI
from twilio.rest import Client

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from cache import RedisCache
import marketplace_tools

app = Flask(__name__)
CORS(app)

AWS_REGION_EXPLICIT = 'us-west-2'

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

try:
	sms_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
	client = OpenAI(api_key=GEMINI_API_KEY, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
	s3_client = boto3.client('s3', region_name=AWS_REGION_EXPLICIT)
	transcribe_client = boto3.client('transcribe', region_name=AWS_REGION_EXPLICIT)
	translate_client = boto3.client('translate', region_name=AWS_REGION_EXPLICIT)
	polly_client = boto3.client('polly', region_name=AWS_REGION_EXPLICIT)
	print(f"AWS Boto3 clients initialized for region: {AWS_REGION_EXPLICIT}")
except NoRegionError:
	print("ERROR: AWS_REGION environment variable is not set. Boto3 clients cannot be initialized.")
except Exception as e:
	print(f"ERROR: Failed to initialize AWS Boto3 clients: {repr(e)}")

cache = RedisCache()

# Configuration for voice processing
S3_BUCKET_NAME = 'farmassist-voice-gateway-audio'
TARGET_LLM_LANGUAGE = 'en'
DEFAULT_FARMER_LANGUAGE = 'hi-IN'
SUPPORTED_TRANSCRIBE_LANGUAGES = [
	'en-US', 'hi-IN', 'gu-IN', 'mr-IN', 'bn-IN',
	'ta-IN', 'te-IN', 'kn-IN', 'ml-IN', 'pa-IN',
]
POLLY_DESCRIBE_VOICES_SUPPORTED_LANGUAGES = [
	'en-IE', 'ar-AE', 'en-US', 'fr-BE', 'en-IN', 'es-MX', 'en-ZA', 'tr-TR', 'ru-RU',
	'ro-RO', 'pt-PT', 'pl-PL', 'nl-NL', 'it-IT', 'is-IS', 'fr-FR', 'fi-FI', 'es-ES',
	'de-DE', 'yue-CN', 'ko-KR', 'en-NZ', 'en-GB-WLS', 'hi-IN', 'de-CH', 'arb',
	'nl-BE', 'cy-GB', 'cs-CZ', 'cmn-CN', 'da-DK', 'en-AU', 'pt-BR', 'nb-NO',
	'sv-SE', 'ja-JP', 'es-US', 'ca-ES', 'fr-CA', 'en-GB', 'de-AT',
]

# Dummy functions that interact with the PostgreSQL database
# These mirror the tool definitions you provided earlier.

@app.route('/add_listing', methods=['POST'])
def add_listing():
	"""API endpoint to add a new item listing."""
	data = request.json
	item_name = data.get('item_name')
	price = data.get('price')
	description = data.get('description')
	seller_name = data.get('seller_name') # New field
	seller_contact = data.get('seller_contact') # New field

	# Basic validation for required fields
	if not item_name or price is None or seller_contact is None:
		return jsonify({"error": "item_name, price, and seller_contact are required"}), 400

	result = create_listing_in_db(
		item_name=item_name,
		price=price,
		description=description,
		seller_name=seller_name,
		seller_contact=seller_contact
	)

	if result.get("status") == "success":
		return jsonify(result), 201
	else:
		return jsonify({"error": result.get("message")}), 500

@app.route('/delete_listing', methods=['POST'])
def delete_listing():
	"""API endpoint to delete an item listing."""
	data = request.json
	listing_id = data.get('listing_id')

	if not listing_id:
		return jsonify({"error": "listing_id is required"}), 400

	result = remove_listing_from_db(listing_id)
	
	if result.get("status") == "success":
		return jsonify(result), 200
	elif result.get("status") == "not_found":
		return jsonify(result), 404
	else:
		return jsonify({"error": result.get("message")}), 500

@app.route('/sell_item', methods=['POST'])
def sell_item():
	"""API endpoint to mark an existing item listing as sold."""
	data = request.json
	listing_id = data.get('listing_id')
	listing_name = data.get('listing_name')
	buyer_contact = data.get('buyer_contact')
	seller_contact = "9876543210"

	if not listing_id:
		return jsonify({"error": "listing_id is required"}), 400

	try:
		conn = get_db_connection()
		cur = conn.cursor()
		query = "SELECT seller_contact FROM listings WHERE id = %s;"
		cur.execute(query, (listing_id,))

		# Fetch the result
		result = cur.fetchone()

		if result:
			seller_contact = str(result[0])
		else:
			print(f"No listing found with ID: {listing_id}")

		cur.execute(
			"""
			UPDATE listings
			SET status = 'sold', updated_at = CURRENT_TIMESTAMP
			WHERE id = %s AND status = 'active'
			RETURNING id, item_name;
			""",
			(listing_id,)
		)
		updated_row = cur.fetchone()
		conn.commit()
		cur.close()
		conn.close()

		if updated_row:
			return jsonify({
				"status": "success",
				"message": f"Listing '{listing_id}' for '{updated_row[1]}' marked as sold.",
				"buyer_id": buyer_id # Still passing buyer_id even if not stored
			}), 200
		else:
			return jsonify({
				"status": "not_found",
				"message": f"Listing '{listing_id}' not found or already sold."
			}), 404
	except Exception as e:
		print(f"Error selling item: {e}")
		return jsonify({"error": str(e)}), 500
	finally:
		sms_message = f"🛍️ Order Received! You have received an order for '{listing_name}'. Call buyer at {buyer_contact}"

		try:
			sms = sms_client.messages.create(
				body=sms_message,
				from_=TWILIO_PHONE_NUMBER,
				to="+91"+seller_contact
			)
			print(f"✅ SMS sent to {to_phone} (SID: {sms.sid})")
			return {"status": "success", "message_sid": sms.sid}
		except Exception as e:
			print(f"❌ SMS failed: {e}")
			return {"status": "error", "message": str(e)}

@app.route('/get_all_listings', methods=['GET'])
def get_all_listings():
	"""API endpoint to retrieve all active item listings."""
	try:
		conn = get_db_connection()
		cur = conn.cursor()
		# Fetch all columns including the new seller_name and seller_contact
		cur.execute("SELECT * FROM listings;")
		
		# Get column names from the cursor description
		columns = [col[0] for col in cur.description]
		
		# Fetch all rows and map them to dictionaries using column names
		listings = [dict(zip(columns, row)) for row in cur.fetchall()]
		
		cur.close()
		conn.close()

		# Convert UUID objects and Decimal objects to JSON-serializable types (string and float)
		for listing in listings:
			if 'id' in listing:
				listing['id'] = str(listing['id'])
			if 'price' in listing:
				listing['price'] = float(listing['price'])
			# seller_contact is NUMERIC in DB, will be int or float in Python; ensure it's simple
			if 'seller_contact' in listing and listing['seller_contact'] is not None:
				listing['seller_contact'] = str(int(listing['seller_contact'])) # Convert to string for phone numbers

		return jsonify({"status": "success", "listings": listings}), 200
	except Exception as e:
		print(f"Error fetching listings: {e}") # Log the error
		return jsonify({"error": str(e)}), 500

@app.route('/process-voice', methods=['POST'])
def process_voice():
	"""
	API endpoint to process voice input, transcribe it,
	send to LLM, get a response, and convert it to speech.
	This integrates the core logic from lambda_function.py.
	"""
	print("Received POST request for voice processing.")
	audio_filename, transcription_job_name, transcript_s3_key = "", "", ""
	detected_language = ""
	polly_voice_id = None
	target_polly_lang = 'hi-IN'
	cache_status = 'miss' # Default cache status

	try:
		body_data = request.json
	except Exception as e:
		print(f"Error decoding request body: {e}")
		return jsonify({'message': f'Failed to process request body: {str(e)}'}), 500

	audio_base64 = body_data.get('audio_data')
	if not audio_base64:
		return jsonify({'message': 'Missing audio_data in request body'}), 400

	# --- 2. Upload Audio to S3 ---
	try:
		audio_bytes = base64.b64decode(audio_base64)
		unique_id = str(uuid.uuid4())
		audio_filename = f"incoming_audio/{unique_id}.mp3"
		s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=audio_filename, Body=audio_bytes)
		audio_s3_uri = f"s3://{S3_BUCKET_NAME}/{audio_filename}"
		print(f"Audio uploaded to S3: {audio_s3_uri}")
	except ClientError as e:
		print(f"S3 Upload Error: {e}")
		return jsonify({'message': 'Failed to upload audio to S3'}), 500

	# --- 3. Convert Voice to Text with Auto Language ID ---
	transcription_job_name = f'voice-to-text-{unique_id}'
	transcribed_text = ""
	transcript_s3_key = f'transcripts/{transcription_job_name}.json'

	try:
		transcribe_client.start_transcription_job(
			TranscriptionJobName=transcription_job_name,
			IdentifyLanguage=True,
			LanguageOptions=SUPPORTED_TRANSCRIBE_LANGUAGES,
			MediaFormat='mp3',
			Media={'MediaFileUri': audio_s3_uri},
			OutputBucketName=S3_BUCKET_NAME,
			OutputKey=transcript_s3_key
		)
		max_attempts = 120
		for i in range(max_attempts):
			job_status_response = transcribe_client.get_transcription_job(TranscriptionJobName=transcription_job_name)
			status = job_status_response['TranscriptionJob']['TranscriptionJobStatus']
			print(f"Transcription status: {status} ({i+1}/{max_attempts})")
			if status == 'COMPLETED':
				detected_language = job_status_response['TranscriptionJob'].get('LanguageCode', DEFAULT_FARMER_LANGUAGE)
				transcript_response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
				transcript_content = json.loads(transcript_response['Body'].read().decode('utf-8'))
				transcribed_text = transcript_content['results']['transcripts'][0]['transcript']
				print(f"Detected Language: {detected_language}")
				print(f"Transcribed Text: {transcribed_text}")
				break
			elif status == 'FAILED':
				raise Exception(job_status_response['TranscriptionJob'].get('FailureReason', 'Unknown reason'))
			time.sleep(5)
		else:
			raise Exception("Transcription job timed out.")
	except Exception as e:
		print(f"Transcribe Error: {e}")
		return jsonify({'message': f'Transcription failed: {str(e)}'}), 500

	# --- 4. Translate Transcribed Text for LLM ---
	text_for_llm = transcribed_text
	source_language_for_translate = detected_language.split('-')[0]
	if source_language_for_translate != TARGET_LLM_LANGUAGE:
		print(f"Translating from {source_language_for_translate} to {TARGET_LLM_LANGUAGE} for LLM.")
		try:
			translate_response = translate_client.translate_text(
				Text=transcribed_text,
				SourceLanguageCode=source_language_for_translate,
				TargetLanguageCode=TARGET_LLM_LANGUAGE
			)
			text_for_llm = translate_response['TranslatedText']
			print(f"Translated Text for LLM: {text_for_llm}")
		except ClientError as e:
			print(f"Translate Error for LLM input: {e}")

	# --- 5. Generate Response with LLM (Caching & Tool Calling) ---
	llm_response_text = ""
	try:
		if (cached_response := cache.get_semantically(text_for_llm)):
			print("⚡ Cache HIT!")
			llm_response_text = cached_response
			cache_status = 'hit'
		else:
			print("🔄 Cache MISS - Calling Gemini with tool support...")
			llm_prompt = (
				f"You are an agricultural assistant. Based on the following farmer's query, provide a concise and helpful response. If farmer wants to sell something, create a listing using add_listing. farmer query: '{text_for_llm}'. "
			)
			messages = [{"role": "user", "content": llm_prompt}]
			
			# Check if marketplace_tools is available before using it
			tools_to_use = marketplace_tools.tools

			response = client.chat.completions.create(
				model="gemini-2.0-flash",
				messages=messages,
				tools=tools_to_use,
				tool_choice="auto"
			)
			
			if marketplace_tools.process_tool_calls(response):
				llm_response_text = "The requested task has been completed." # Placeholder for tool action
			else:
				llm_response_text = response.choices[0].message.content
				cache.set(text_for_llm, llm_response_text) # Cache new responses
		
		print(f"LLM Response: {llm_response_text}")

	except Exception as e:
		print(f"Error interacting with LLM: {e}")
		llm_response_text = "I'm sorry, I could not generate an a response at this time."

	# --- 6. Translate LLM Response Back to Farmer's Language ---
	final_response_text = llm_response_text

	# If detected language is a regional Indian one without direct Polly support, translate to Hindi or English
	if detected_language.startswith(('gu-', 'mr-', 'bn-', 'pa-')):
		 target_polly_lang = 'hi-IN'
	elif detected_language.startswith(('en-', 'ta-', 'te-', 'kn-', 'ml-')):
		 target_polly_lang = 'en-IN'
	
	if target_polly_lang.split('-')[0] != TARGET_LLM_LANGUAGE:
		print(f"Translating response from {TARGET_LLM_LANGUAGE} to {target_polly_lang} for Polly.")
		try:
			translate_response = translate_client.translate_text(
				Text=llm_response_text, SourceLanguageCode=TARGET_LLM_LANGUAGE, TargetLanguageCode=target_polly_lang
			)
			final_response_text = translate_response['TranslatedText']
			print(f"Translated Response for Farmer: {final_response_text}")
		except ClientError as e:
			print(f"Translate Error for TTS output: {e}")
	
	# --- 7. Convert Text to Speech with Advanced Voice Selection ---
	audio_stream = None
	try:
		polly_engine = 'neural' # Prefer neural voices
		
		# Specific high-quality voices
		if target_polly_lang == 'hi-IN': polly_voice_id = 'Kajal'
		elif target_polly_lang == 'en-IN': polly_voice_id = 'Kajal'
		
		# Find a voice if not hardcoded
		# if not polly_voice_id:
		#     if target_polly_lang in POLLY_DESCRIBE_VOICES_SUPPORTED_LANGUAGES:
		#         try: # Try for a neural voice first
		#             voices = polly_client.describe_voices(LanguageCode=target_polly_lang, Engine='neural')['Voices']
		#             if voices: polly_voice_id = voices[0]['Id']
		#         except ClientError: # Fallback to standard
		#             voices = polly_client.describe_voices(LanguageCode=target_polly_lang, Engine='standard')['Voices']
		#             if voices:
		#                 polly_voice_id = voices[0]['Id']
		#                 polly_engine = 'standard'
		
		# Final fallback to a default English voice
		# if not polly_voice_id:
		#     print(f"No Polly voice for '{target_polly_lang}'. Falling back to en-US.")
		#     polly_voice_id = 'Kajal'
		#     target_polly_lang = 'en-IN'
		#     final_response_text = llm_response_text # Use original English text

		print(f"Using Polly voice '{polly_voice_id}' ({polly_engine}) for language '{target_polly_lang}'.")
		polly_response = polly_client.synthesize_speech(
			Text=final_response_text, OutputFormat='mp3', VoiceId=polly_voice_id,
			LanguageCode=target_polly_lang, Engine=polly_engine
		)
		audio_stream = polly_response['AudioStream'].read()
		print("Speech synthesized with Polly.")
	except Exception as e:
		print(f"Polly Synthesis Error: {e}")
		return jsonify({'message': 'Failed during speech synthesis.'}), 500

	# --- 8. Clean up S3 files ---
	try:
		s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=audio_filename)
		s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=transcript_s3_key)
		print("Cleaned up temporary S3 files.")
	except ClientError as e:
		print(f"Warning: Failed to cleanup S3 objects: {e}")

	# --- 9. Return Synthesized Audio Response ---
	return jsonify({
		'message': 'Processing complete',
		'transcribed_text': transcribed_text,
		'llm_response': llm_response_text,
		'final_spoken_text': final_response_text,
		'audio_response_base64': base64.b64encode(audio_stream).decode('utf-8') if audio_stream else None,
		'detected_language': detected_language,
		'cache_status': cache_status,
		'target_polly_lang': target_polly_lang,
		'polly_voice_id': polly_voice_id
	}), 200

if __name__ == '__main__':
	# Make sure your .env file is loaded correctly by database.py
	# and the Flask environment is set up.
	# For local development, debug=True is useful. Host 0.0.0.0 makes it accessible
	# from other devices on the network.
	app.run(debug=True, host='0.0.0.0', port=5002)
