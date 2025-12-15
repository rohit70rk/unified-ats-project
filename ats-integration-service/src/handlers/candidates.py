import json
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

def handler(event, context):
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        
        # Validate that job_id is present (Required for "Attaching" to a job)
        required = ['name', 'email', 'job_id']
        if not all(field in body for field in required):
            return error("Missing required fields: name, email, job_id", 400)

        client = ATSClient()
        
        # Pass the data to the service
        result = client.create_candidate(body)
        
        return success(result, 201)
    except Exception as e:
        return error(f"Failed to create candidate: {str(e)}")