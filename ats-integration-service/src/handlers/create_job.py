import json
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

def handler(event, context):
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        
        # Validation
        if not body.get('title') or not body.get('location'):
            return error("Missing required fields: title, location", 400)

        # Call Service
        client = ATSClient()
        result = client.create_job(body)
        
        return success(result, 201)
    except Exception as e:
        return error(f"Failed to create job: {str(e)}")