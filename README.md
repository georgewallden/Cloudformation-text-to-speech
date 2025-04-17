This application demonstrates a serverless API using AWS API Gateway and Lambda to convert text into speech. The Lambda function utilizes Amazon Polly for audio synthesis and returns a URL to the generated MP3 file stored in S3.

Test with the following http request: Invoke-WebRequest -Uri 'https://1rg1orsv77.execute-api.us-east-1.amazonaws.com/live/synthesize' -Method POST -ContentType 'application/json' -Body '{"text": "Testing the Cloudformation text to speech app by George Wallden.", "voice": "Joanna"}'
