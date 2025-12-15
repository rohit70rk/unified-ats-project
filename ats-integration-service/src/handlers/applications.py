import logging
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {}) or {}
        job_id = params.get('job_id')
        
        if not job_id:
            logger.warning("Missing job_id in applications request")
            return error("Missing required query parameter: job_id", 400)

        logger.info(f"Fetching applications for Job ID: {job_id}")
        client = ATSClient()
        apps = client.get_applications(job_id)
        
        return success(apps)
    except Exception as e:
        logger.error(f"Handler Error (getApplications): {str(e)}")
        return error(f"Failed to fetch applications: {str(e)}")