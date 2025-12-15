import os
import requests
import json
import time
from datetime import datetime, timedelta
from requests.exceptions import RequestException

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

        print("DEBUG: Fetching NEW Token from Zoho...")
        params = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        try:
            response = requests.post(self.auth_url, params=params, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Authentication Failed: {response.text}")
            
            data = response.json()
            _TOKEN_CACHE["access_token"] = data['access_token']
            _TOKEN_CACHE["expires_at"] = current_time + 3300
            return data['access_token']
        except RequestException as e:
            print(f"Network Error during Auth: {str(e)}")
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
                    all_jobs.append({
                        "id": job.get('id'),
                        "title": job.get('Job_Opening_Name'),
                        "location": job.get('City', 'Remote'),
                        "status": job.get('Job_Opening_Status', 'OPEN').upper(),
                        "external_url": job.get('Job_Opening_URL', ''),
                        "description": job.get('Job_Description', 'No description provided.')
                    })
                
                info = response.json().get('info', {})
                if not info.get('more_records'): has_more = False
                else: page += 1

            return all_jobs
        except Exception as e:
            print(f"DEBUG: Error in fetch_jobs: {str(e)}")
            raise e

    def create_candidate(self, candidate_data):
        url_create = f"{self.base_url}/Candidates"
        job_id = candidate_data.get('job_id')
        
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
            print(f"DEBUG: Creating candidate {first_name} {last_name}...")
            response = requests.post(url_create, headers=self._headers(), json=zoho_payload, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('data') and result['data'][0]['status'] == 'success':
                    candidate_id = result['data'][0]['details']['id']
                    print(f"DEBUG: Created Candidate ID: {candidate_id}")
                elif result.get('data') and result['data'][0]['code'] == 'DUPLICATE_DATA':
                    print("DEBUG: Candidate exists. Fetching existing ID by Email...")
                    candidate_id = self._get_candidate_id_by_email(candidate_data.get('email'))
                else:
                    raise Exception(f"Zoho Validation: {json.dumps(result)}")
            else:
                raise Exception(f"Zoho Create Failed: {response.text}")

            if candidate_id and job_id:
                self._associate_candidate_action(job_id, candidate_id)
                return {"id": candidate_id, "message": "Candidate created and associated successfully"}
            
            return {"id": candidate_id, "message": "Candidate created (No Job ID provided)"}

        except Exception as e:
            print(f"DEBUG: Exception in create_candidate: {str(e)}")
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
        
        print(f"DEBUG: Associating Candidate {candidate_id} to Job {job_id} using 'actions/associate'...")
        try:
            response = requests.put(url_associate, headers=self._headers(), json=payload, timeout=10)
            if response.status_code == 200:
                print("DEBUG: Association Successful.")
            else:
                print(f"DEBUG: Association HTTP Error: {response.text}")
        except Exception as e:
            print(f"DEBUG: Association Exception: {str(e)}")

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
        print(f"DEBUG: Searching Applications for Job_ID: {job_id}")
        url = f"{self.base_url}/Applications/search"
        
        try:
            all_apps = []
            page = 1
            has_more = True
            
            while has_more:
                # Use the system field ($Job_Opening_Id) we discovered in your logs
                params = {
                    "criteria": f"(($Job_Opening_Id:equals:{job_id}))",
                    "page": page, 
                    "per_page": 200
                }
                
                response = requests.get(url, headers=self._headers(), params=params, timeout=10)
                
                if response.status_code == 204: break 
                if response.status_code != 200:
                    print(f"DEBUG: Search Applications Error: {response.text}")
                    break
                
                data = response.json().get('data', [])
                if not data: break
                
                # Manual filtering to ensure we only get candidates for THIS job
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
                if not info.get('more_records'): has_more = False
                else: page += 1
            
            print(f"DEBUG: Found {len(all_apps)} applications after filtering.")
            return self._map_applications(all_apps)
            
        except Exception as e:
            print(f"DEBUG: Exception in get_applications: {str(e)}")
            return []

    def _map_applications(self, data):
        unified_apps = []
        for app in data:
            # --- 1. GET CANDIDATE NAME ---
            cand_name = "Unknown Candidate"
            
            # Priority 1: Check the 'Candidate_Name' Lookup Object (Most common in Zoho)
            cand_lookup = app.get('Candidate_Name')
            if isinstance(cand_lookup, dict):
                cand_name = cand_lookup.get('name')
            elif isinstance(cand_lookup, str):
                cand_name = cand_lookup
            
            # Priority 2: Check 'Full_Name' field if lookup failed
            if cand_name == "Unknown Candidate" and app.get('Full_Name'):
                cand_name = app.get('Full_Name')

            # Priority 3: Parse 'Application_Name' (e.g. "Rohit for Python Dev")
            if cand_name == "Unknown Candidate" and app.get('Application_Name'):
                app_name = app.get('Application_Name')
                if " for " in app_name:
                    cand_name = app_name.split(" for ")[0]
                else:
                    cand_name = app_name

            # --- 2. GET CANDIDATE ID ---
            # We look for 'Candidate_ID' (Readable ID like ZR_18_CAND) 
            # or fallback to the system '$Candidate_Id'
            cand_id = app.get('Candidate_ID')
            if not cand_id:
                cand_id = app.get('$Candidate_Id', 'N/A')

            # --- 3. STATUS MAPPING ---
            raw_status = app.get('Application_Status', 'Associated')
            status_upper = raw_status.upper()
            if status_upper == "ASSOCIATED":
                status_upper = "APPLIED"

            unified_apps.append({
                "id": app.get('id'), # System ID of the Application
                "candidate_id": cand_id, # Readable Candidate ID (ZR_...)
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

        zoho_payload = {
            "data": [{
                "Posting_Title": job_data.get('title'),
                "Job_Opening_Name": job_data.get('title'),
                "Target_Date": target_date,
                "Client_Name": "My company", 
                "City": job_data.get('location'),
                "Job_Description": desc,
                "Job_Opening_Status": "In-progress",
                "Industry": "Software",
                "Job_Type": "Full time",
                "NumberOfPositions": 1
            }]
        }
        try:
            response = requests.post(url, headers=self._headers(), json=zoho_payload, timeout=10)
            if response.status_code not in [200, 201]:
                raise Exception(f"Zoho Error: {response.text}")
            return {"message": "Job created successfully"}
        except Exception as e:
            print(f"DEBUG: Exception in create_job: {str(e)}")
            raise Exception(f"Error creating job: {str(e)}")