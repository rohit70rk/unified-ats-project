import json
import logging
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        # Parse body
        body = json.loads(event.get('body', '{}'))
        required = ['first_name', 'last_name', 'email', 'job_id']
        
        # Check if all required fields are present
        missing = [field for field in required if field not in body]
        if missing:
             logger.warning(f"Missing fields in candidate creation: {missing}")
             return error(f"Missing required fields: {', '.join(missing)}", 400)

        logger.info(f"Creating candidate: {body.get('email')} for Job {body.get('job_id')}")
        client = ATSClient()
        result = client.create_candidate(body)
        
        return success(result, 201)
    except Exception as e:
        logger.error(f"Handler Error (createCandidate): {str(e)}")
        return error(f"Failed to create candidate: {str(e)}")