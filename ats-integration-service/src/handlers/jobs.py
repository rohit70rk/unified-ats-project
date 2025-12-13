from src.services.ats_client import ATSClient
from src.utils.responses import success, error

def handler(event, context):
    try:
        client = ATSClient()
        jobs = client.fetch_jobs()
        return success(jobs)
    except Exception as e:
        return error(f"Failed to fetch jobs: {str(e)}")