import os
import requests
import json
from requests.exceptions import RequestException

class ATSClient:
    def __init__(self):
        # Load credentials from .env
        self.client_id = os.environ.get('ZOHO_CLIENT_ID')
        self.client_secret = os.environ.get('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.environ.get('ZOHO_REFRESH_TOKEN')
        self.base_url = os.environ.get('ZOHO_BASE_URL')
        
        # Auth URL for India Data Center (matches your screenshot)
        self.auth_url = "https://accounts.zoho.in/oauth/v2/token"
        
    def _get_access_token(self):
        """
        Exchanges the Refresh Token for a temporary Access Token.
        Includes error handling for network failures.
        """
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(self.auth_url, params=params, timeout=10)
            
            # Handle non-200 responses specifically for Auth
            if response.status_code != 200:
                print(f"Auth Error: {response.text}")
                raise Exception(f"Authentication Failed (Status {response.status_code})")
            
            return response.json()['access_token']
            
        except RequestException as e:
            # Catch network errors (DNS, Timeout, No Internet)
            print(f"Network Error during Auth: {str(e)}")
            raise Exception("Network error while connecting to Zoho Auth service")

    def _headers(self):
        token = self._get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }

    def fetch_jobs(self):
        """
        Fetches job openings. Handles 204 (No Content) gracefully.
        """
        url = f"{self.base_url}/JobOpenings"
        
        try:
            response = requests.get(url, headers=self._headers(), timeout=10)
            
            # --- FIX: Handle Empty List Gracefully ---
            if response.status_code == 204:
                return [] 
            
            if response.status_code != 200:
                raise Exception(f"Zoho API Error ({response.status_code}): {response.text}")
                
            data = response.json().get('data', [])
            
            # Transform to Unified API Standard
            unified_jobs = []
            for job in data:
                unified_jobs.append({
                    "id": job.get('id'),
                    "title": job.get('Job_Opening_Name'),
                    "location": job.get('City', 'Remote'),
                    "status": job.get('Job_Opening_Status', 'OPEN').upper(),
                    "external_url": job.get('Job_Opening_URL', '')
                })
            return unified_jobs

        except RequestException as e:
            print(f"Network Error fetching jobs: {str(e)}")
            raise Exception("Failed to connect to Zoho JobOpenings endpoint")

    def create_candidate(self, candidate_data):
        url = f"{self.base_url}/Candidates"
        
        zoho_payload = {
            "data": [{
                "First_Name": candidate_data.get('name').split(' ')[0],
                "Last_Name": " ".join(candidate_data.get('name').split(' ')[1:]) or "Candidate",
                "Email": candidate_data.get('email'),
                "Mobile": candidate_data.get('phone'),
                "Source": "Unified API"
            }]
        }
        
        try:
            response = requests.post(url, headers=self._headers(), json=zoho_payload, timeout=10)
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Zoho Create Failed: {response.text}")
                
            result = response.json()
            
            # Check for inner Zoho logic errors
            if result.get('data') and result['data'][0]['status'] == 'error':
                 raise Exception(f"Zoho Validation: {json.dumps(result['data'][0])}")

            new_candidate_id = result['data'][0]['details']['id']
            
            # Associate with Job (Best Effort)
            job_id = candidate_data.get('job_id')
            if job_id:
                 self._associate_candidate(new_candidate_id, job_id)
                 
            return {"id": new_candidate_id, "message": "Candidate created successfully"}
            
        except RequestException as e:
            raise Exception(f"Network error creating candidate: {str(e)}")

    def _associate_candidate(self, candidate_id, job_id):
        """Helper method to link candidate to job"""
        try:
            associate_url = f"{self.base_url}/JobOpenings/{job_id}/actions/associate"
            assoc_payload = {
                "data": [{
                    "ids": [candidate_id],
                    "comments": "Applied via Unified API"
                }]
            }
            requests.put(associate_url, headers=self._headers(), json=assoc_payload, timeout=5)
        except Exception as e:
            print(f"Warning: Failed to associate candidate (Non-critical): {e}")

    def get_applications(self, job_id):
        url = f"{self.base_url}/Candidates/search"
        params = {"criteria": f"((Job_Openings.id:equals:{job_id}))"}
        
        try:
            response = requests.get(url, headers=self._headers(), params=params, timeout=10)
            
            if response.status_code == 204:
                return []
                
            if response.status_code != 200:
                 raise Exception(f"Search Failed: {response.text}")

            data = response.json().get('data', [])
            unified_apps = []
            for cand in data:
                unified_apps.append({
                    "id": cand.get('id'),
                    "candidate_name": f"{cand.get('First_Name')} {cand.get('Last_Name')}",
                    "email": cand.get('Email'),
                    "status": cand.get('Candidate_Status', 'APPLIED')
                })
            return unified_apps
        except RequestException as e:
            raise Exception(f"Network error searching applications: {str(e)}")