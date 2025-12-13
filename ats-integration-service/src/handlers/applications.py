from src.services.ats_client import ATSClient
from src.utils.responses import success, error

def handler(event, context):
    try:
        # Get query parameters
        params = event.get('queryStringParameters', {}) or {}
        job_id = params.get('job_id')
        
        if not job_id:
            return error("Missing required query parameter: job_id", 400)

        client = ATSClient()
        apps = client.get_applications(job_id)
        
        return success(apps)
    except Exception as e:
        return error(f"Failed to fetch applications: {str(e)}")