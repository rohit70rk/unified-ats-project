import os
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from requests.exceptions import RequestException

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- GLOBAL CACHE ---
_TOKEN_CACHE = {
    "access_token": None,
    "expires_at": 0
}

class ATSClient:
    def __init__(self):
        self.client_id = os.environ.get('ZOHO_CLIENT_ID')
        self.client_secret = os.environ.get('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.environ.get('ZOHO_REFRESH_TOKEN')
        self.base_url = os.environ.get('ZOHO_BASE_URL')
        self.auth_url = "https://accounts.zoho.in/oauth/v2/token"
        
    def _get_access_token(self):
        global _TOKEN_CACHE
        current_time = time.time()
        if _TOKEN_CACHE["access_token"] and current_time < _TOKEN_CACHE["expires_at"]:
            return _TOKEN_CACHE["access_token"]

        logger.info("Refreshing Zoho Access Token")
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        try:
            response = requests.post(self.auth_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'access_token' not in data:
                 raise Exception(f"No access token in response: {data}")

            _TOKEN_CACHE["access_token"] = data['access_token']
            _TOKEN_CACHE["expires_at"] = current_time + 3300 # Buffer before 1 hour expiry
            return data['access_token']
        except RequestException as e:
            logger.error(f"Auth Network Error: {str(e)}")
            raise Exception("Network error while connecting to Zoho Auth service")

    def _headers(self):
        token = self._get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Content-Type": "application/json"
        }

    def fetch_jobs(self):
        url = f"{self.base_url}/JobOpenings"
        all_jobs = []
        page = 1
        has_more = True

        try:
            while has_more:
                params = {"page": page, "per_page": 200}
                response = requests.get(url, headers=self._headers(), params=params, timeout=10)
                
                if response.status_code == 204: break
                if response.status_code != 200:
                    raise Exception(f"Zoho API Error ({response.status_code}): {response.text}")
                
                data = response.json().get('data', [])
                if not data: break
                
                for job in data:
                    city = job.get('City', '')
                    country = job.get('Country', '')
                    remote = job.get('Remote_Job', False)
                    
                    if remote:
                        loc_display = "Remote"
                    elif city and country:
                        loc_display = f"{city}, {country}"
                    elif city:
                        loc_display = city
                    elif country:
                        loc_display = country
                    else:
                        loc_display = "Location not specified"

                    all_jobs.append({
                        "id": job.get('id'),
                        "title": job.get('Job_Opening_Name'),
                        "location": loc_display,
                        "status": job.get('Job_Opening_Status', 'OPEN').upper(),
                        "external_url": job.get('Job_Opening_URL', ''),
                        "description": job.get('Job_Description', 'No description provided.')
                    })
                
                info = response.json().get('info', {})
                if not info.get('more_records'): 
                    has_more = False
                else: 
                    page += 1

            return all_jobs
        except Exception as e:
            logger.error(f"Error in fetch_jobs: {str(e)}")
            raise e

    def create_candidate(self, candidate_data):
        url_create = f"{self.base_url}/Candidates"
        job_id = candidate_data.get('job_id')
        first_name = candidate_data.get('first_name')
        last_name = candidate_data.get('last_name')
        
        if not first_name or not last_name:
             full_name = candidate_data.get('name', 'Unknown Candidate')
             parts = full_name.split(' ')
             first_name = parts[0]
             last_name = " ".join(parts[1:]) if len(parts) > 1 else "Candidate"

        candidate_record = {
            "First_Name": first_name,
            "Last_Name": last_name,
            "Email": candidate_data.get('email'),
            "Mobile": candidate_data.get('phone'),
            "Website": candidate_data.get('resume_url', ''),
            "Source": "Unified API"
        }

        zoho_payload = {"data": [candidate_record]}
        candidate_id = None

        try:
            response = requests.post(url_create, headers=self._headers(), json=zoho_payload, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('data') and result['data'][0]['status'] == 'success':
                    candidate_id = result['data'][0]['details']['id']
                elif result.get('data') and result['data'][0]['code'] == 'DUPLICATE_DATA':
                    logger.info("Duplicate candidate detected. Fetching existing ID.")
                    candidate_id = self._get_candidate_id_by_email(candidate_data.get('email'))
                else:
                    raise Exception(f"Zoho Validation Failed: {json.dumps(result)}")
            else:
                raise Exception(f"Zoho Create Failed: {response.text}")

            if candidate_id and job_id:
                self._associate_candidate_action(job_id, candidate_id)
                return {"id": candidate_id, "message": "Candidate created and associated successfully"}
            
            return {"id": candidate_id, "message": "Candidate created (No Job ID provided)"}

        except Exception as e:
            logger.error(f"Error in create_candidate: {str(e)}")
            raise Exception(f"Error processing candidate: {str(e)}")

    def _associate_candidate_action(self, job_id, candidate_id):
        url_associate = f"{self.base_url}/Candidates/actions/associate"
        payload = {
            "data": [{
                "ids": [str(candidate_id)],
                "jobids": [str(job_id)],
                "comments": "Associated via Unified ATS"
            }]
        }
        
        try:
            response = requests.put(url_associate, headers=self._headers(), json=payload, timeout=10)
            if response.status_code != 200:
                logger.warning(f"Association failed: {response.text}")
        except Exception as e:
            logger.error(f"Association Exception: {str(e)}")

    def _get_candidate_id_by_email(self, email):
        url = f"{self.base_url}/Candidates/search"
        params = {"criteria": f"(Email:equals:{email})"}
        try:
            response = requests.get(url, headers=self._headers(), params=params)
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data: return data[0]['id']
        except Exception:
            pass
        return None

    def get_applications(self, job_id):
        url = f"{self.base_url}/Applications/search"
        
        try:
            all_apps = []
            page = 1
            has_more = True
            
            while has_more:
                # We still send the criteria to attempt server-side filtering
                params = {
                    "criteria": f"(($Job_Opening_Id:equals:{job_id}))",
                    "page": page, 
                    "per_page": 200
                }
                
                response = requests.get(url, headers=self._headers(), params=params, timeout=10)
                
                if response.status_code == 204: break 
                if response.status_code != 200:
                    logger.error(f"Search Applications Error: {response.text}")
                    break
                
                data = response.json().get('data', [])
                if not data: break
                
                # --- RESTORED MANUAL FILTERING ---
                # This ensures we STRICTLY only return apps for the requested Job ID
                # even if the API returns mixed results.
                for app in data:
                    app_job_id = None
                    
                    if app.get('$Job_Opening_Id'):
                        app_job_id = str(app.get('$Job_Opening_Id'))
                    
                    if not app_job_id and app.get('Job_Opening_ID'):
                        val = app.get('Job_Opening_ID')
                        if isinstance(val, dict):
                            app_job_id = str(val.get('id'))
                        else:
                            app_job_id = str(val)

                    if app_job_id and app_job_id == str(job_id):
                        all_apps.append(app)

                info = response.json().get('info', {})
                if not info.get('more_records'): 
                    has_more = False
                else: 
                    page += 1
            
            return self._map_applications(all_apps)
            
        except Exception as e:
            logger.error(f"Exception in get_applications: {str(e)}")
            return []

    def _map_applications(self, data):
        unified_apps = []
        for app in data:
            # --- 1. GET CANDIDATE NAME ---
            cand_name = "Unknown Candidate"
            
            cand_lookup = app.get('Candidate_Name')
            if isinstance(cand_lookup, dict):
                cand_name = cand_lookup.get('name')
            elif isinstance(cand_lookup, str):
                cand_name = cand_lookup
            
            if cand_name == "Unknown Candidate" and app.get('Full_Name'):
                cand_name = app.get('Full_Name')

            if cand_name == "Unknown Candidate" and app.get('Application_Name'):
                app_name = app.get('Application_Name')
                cand_name = app_name.split(" for ")[0] if " for " in app_name else app_name

            # --- 2. GET CANDIDATE ID ---
            cand_id = app.get('Candidate_ID')
            if not cand_id:
                cand_id = app.get('$Candidate_Id', 'N/A')

            # --- 3. STATUS MAPPING ---
            raw_status = app.get('Application_Status', 'Associated')
            status_upper = raw_status.upper()
            if status_upper == "ASSOCIATED":
                status_upper = "APPLIED"

            unified_apps.append({
                "id": app.get('id'),
                "candidate_id": cand_id,
                "candidate_name": cand_name,
                "email": app.get('Email', 'No Email'),
                "status": status_upper
            })
        return unified_apps

    def create_job(self, job_data):
        url = f"{self.base_url}/JobOpenings"
        target_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        desc = job_data.get('description', 'No description provided.')
        
        if len(desc) < 150:
            desc += " " + ("(Padding for Zoho minimum length requirement) " * 5)
            
        is_remote = job_data.get('remote', False)
        city = job_data.get('city', '')
        country = job_data.get('country', '')

        job_record = {
            "Posting_Title": job_data.get('title'),
            "Job_Opening_Name": job_data.get('title'),
            "Target_Date": target_date,
            "Client_Name": "My company", 
            "Job_Description": desc,
            "Job_Opening_Status": "In-progress",
            "Industry": "Software",
            "Job_Type": "Full time",
            "NumberOfPositions": 1,
            "Remote_Job": is_remote,
        }

        if not is_remote:
            job_record["City"] = city
            job_record["Country"] = country

        zoho_payload = {"data": [job_record]}

        try:
            response = requests.post(url, headers=self._headers(), json=zoho_payload, timeout=10)
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Zoho Error: {response.text}")
                
            response_json = response.json()
            if response_json.get('data') and response_json['data'][0].get('status') == 'error':
                 logger.error(f"Zoho Logic Error: {json.dumps(response_json)}")
                 raise Exception(f"Zoho Error: {json.dumps(response_json)}")

            return {"message": "Job created successfully"}
        except Exception as e:
            logger.error(f"Exception in create_job: {str(e)}")
            raise Exception(f"Error creating job: {str(e)}")