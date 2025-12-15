import json
import logging
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        
        if not body.get('title'):
            return error("Missing required field: title", 400)

        if not body.get('remote') and (not body.get('city') or not body.get('country')):
            return error("City and Country are required for non-remote jobs.", 400)

        logger.info(f"Creating new job: {body.get('title')}")
        client = ATSClient()
        result = client.create_job(body)
        
        return success(result, 201)
    except Exception as e:
        logger.error(f"Handler Error (createJob): {str(e)}")
        return error(f"Failed to create job: {str(e)}")