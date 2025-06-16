import unittest
from unittest.mock import patch, MagicMock
import base64
import json

# Import your lambda function module
import lambda_function

class TestLambdaFunction(unittest.TestCase):
    
    @patch('lambda_function.s3_client')
    @patch('lambda_function.transcribe_client')
    @patch('lambda_function.translate_client')
    @patch('lambda_function.polly_client')
    @patch('lambda_function.urlopen')
    def test_lambda_handler_success(self, mock_urlopen, mock_polly, mock_translate, mock_transcribe, mock_s3):
        # Mock event input with base64 audio and language code
        fake_audio = base64.b64encode(b"FAKEAUDIO").decode('utf-8')
        mock_event = {
            "body": json.dumps({
                "audio_data": fake_audio,
                "farmer_language_code": "hi"
            })
        }

        # S3 put/get mocks
        mock_s3.put_object.return_value = {}
        mock_s3.get_object.return_value = {
            'Body': MagicMock(read=MagicMock(return_value=json.dumps({
                'results': {'transcripts': [{'transcript': 'fake transcription'}]}
            }).encode('utf-8')))
        }

        # Transcribe job status mock
        mock_transcribe.get_transcription_job.side_effect = [
            {'TranscriptionJob': {'TranscriptionJobStatus': 'IN_PROGRESS'}},
            {'TranscriptionJob': {'TranscriptionJobStatus': 'COMPLETED'}}
        ]

        # Translate mock
        mock_translate.translate_text.side_effect = [
            {'TranslatedText': 'translated for LLM'},
            {'TranslatedText': 'translated for farmer'}
        ]

        # Gemini API mock
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "candidates": [{
                "content": {
                    "parts": [{"text": "AI Response"}]
                }
            }]
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Polly mock
        mock_polly.synthesize_speech.return_value = {
            'AudioStream': MagicMock(read=MagicMock(return_value=b'FAKEAUDIOOUTPUT'))
        }

        # Run handler
        result = lambda_function.lambda_handler(mock_event, None)
        body = json.loads(result['body'])

        # Assertions
        self.assertEqual(result['statusCode'], 200)
        self.assertIn('transcribed_text', body)
        self.assertIn('audio_response_base64', body)
        self.assertEqual(body['llm_response'], 'AI Re
