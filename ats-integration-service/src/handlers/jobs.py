import logging
from src.services.ats_client import ATSClient
from src.utils.responses import success, error

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    try:
        logger.info("Received request to fetch jobs")
        client = ATSClient()
        jobs = client.fetch_jobs()
        return success(jobs)
    except Exception as e:
        logger.error(f"Failed to fetch jobs: {str(e)}")
        return error(f"Failed to fetch jobs: {str(e)}")