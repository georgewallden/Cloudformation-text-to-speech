# index.py
import boto3
import os
import json
import uuid # To generate unique filenames

# Initialize clients outside the handler for reuse
polly = boto3.client('polly')
s3 = boto3.client('s3')

# Get the bucket name from environment variable
OUTPUT_BUCKET = os.environ['OUTPUT_BUCKET_NAME']
# Determine region dynamically (best practice)
AWS_REGION = os.environ['AWS_REGION']

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        # Expect text in the request body (Lambda Proxy Integration V2.0 format)
        body = json.loads(event.get('body', '{}'))
        text_to_synthesize = body.get('text')
        voice_id = body.get('voice', 'Joanna') # Default to Joanna if not specified

        if not text_to_synthesize:
            raise ValueError("Missing 'text' property in request body")

        # --- Call Polly ---
        try:
            response = polly.synthesize_speech(
                Text=text_to_synthesize,
                OutputFormat='mp3',
                VoiceId=voice_id,
                Engine='neural' # Use the better neural engine if available for the voice
            )
        except polly.exceptions.UnsupportedSsmlException:
             # Fallback to standard engine if neural is not supported for the voice/language
             print(f"Neural engine not supported for voice {voice_id}, falling back to standard.")
             response = polly.synthesize_speech(
                Text=text_to_synthesize,
                OutputFormat='mp3',
                VoiceId=voice_id
            )

        audio_stream = response.get('AudioStream')

        if not audio_stream:
             raise Exception("Polly did not return an audio stream.")

        # --- Upload to S3 ---
        # Generate a unique key (filename) for the MP3 file
        output_key = f"{uuid.uuid4()}.mp3"

        print(f"Uploading audio stream to s3://{OUTPUT_BUCKET}/{output_key}")

        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=audio_stream.read(), # Read the stream content
            ContentType='audio/mpeg',
            ACL='public-read' # Make the object publicly readable
        )

        # --- Construct Public S3 URL ---
        # Different URL formats depending on region (e.g., us-east-1 vs others)
        if AWS_REGION == 'us-east-1':
             output_url = f"https://{OUTPUT_BUCKET}.s3.amazonaws.com/{output_key}"
        else:
             output_url = f"https://{OUTPUT_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{output_key}"

        print(f"Successfully generated audio: {output_url}")

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # Add CORS header for API response
            },
            'body': json.dumps({'audioUrl': output_url})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
             },
            'body': json.dumps({'message': f"Internal server error: {str(e)}"})
        }