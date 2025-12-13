import json
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

def handler(event, context):
    try:
        # Parse body (Serverless passes body as a string)
        body = json.loads(event.get('body', '{}'))
        
        # Basic Validation
        required = ['name', 'email', 'job_id']
        if not all(field in body for field in required):
            return error("Missing required fields: name, email, job_id", 400)

        client = ATSClient()
        result = client.create_candidate(body)
        
        return success(result, 201)
    except Exception as e:
        return error(f"Failed to create candidate: {str(e)}")