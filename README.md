## Unified ATS Integration Service

A Serverless Python microservice that acts as a Unified API for recruitment data. It normalizes data from **Zoho Recruit** into a standardized JSON format for Jobs, Candidates, and Applications.

## 📌 Features
- **Unified Schema:** Maps Zoho's specific statuses (e.g., "In-progress") to standard statuses (`OPEN`, `CLOSED`, `DRAFT`).
- **Candidate Creation:** Accepts a standard payload and splits names/logic for Zoho automatically.
- **Application Tracking:** Fetches applicants for a specific job with normalized statuses (`APPLIED`, `SCREENING`, `HIRED`, `REJECTED`).
- **Secure:** Uses Environment Variables for credentials.

## 🛠️ 1. Setup Zoho Recruit (Sandbox/Trial)
1.  **Sign Up:** Go to [Zoho Recruit](https://www.zoho.com/recruit/) and sign up for a **Free Trial** (Enterprise Edition is recommended for full API access).
2.  **Access Developer Space:**
    * Log in to Zoho Recruit.
    * Click the **Setup (Gear Icon)** in the top right.
    * Under **Developer Space**, click **APIs**.
    * Note your `ZOHO_BASE_URL` (e.g., `https://recruit.zoho.in/recruit/v2` or `https://recruit.zoho.com/recruit/v2`).

## 🔑 2. Generate API Keys (OAuth 2.0)
Since this is a server-side app, you need a **Self-Client** or **Server-based** OAuth flow.

1.  Go to the [Zoho API Console](https://api-console.zoho.com/).
2.  Click **Add Client** -> **Server-based Applications**.
3.  **Fill Details:**
    * **Client Name:** `UnifiedATS`
    * **Homepage URL:** `http://localhost:3000`
    * **Authorized Redirect URIs:** `http://localhost:3000/callback`
4.  Click **Create**. Copy the **Client ID** and **Client Secret**.
5.  **Generate Refresh Token:**
    * In your browser, visit this URL (replace `{YOUR_CLIENT_ID}`):
        [https://accounts.zoho.com/oauth/v2/auth?scope=ZohoRecruit.modules.ALL&client_id=](https://accounts.zoho.com/oauth/v2/auth?scope=ZohoRecruit.modules.ALL&client_id=){YOUR_CLIENT_ID}&response_type=code&access_type=offline&redirect_uri=http://localhost:3000/callback
    * Click **Accept**. You will be redirected to a blank page. **Copy the `code=` parameter** from the URL bar.
    * Run this `curl` command immediately (code expires in 60s):
        curl -X POST "[https://accounts.zoho.com/oauth/v2/token?code=](https://accounts.zoho.com/oauth/v2/token?code=){YOUR_CODE}&client_id={YOUR_CLIENT_ID}&client_secret={YOUR_SECRET}&redirect_uri=http://localhost:3000/callback&grant_type=authorization_code"
    * Save the `refresh_token` from the JSON response.

## 💻 3. Local Installation & Configuration

### Prerequisites
* **Node.js** (for Serverless Framework)
* **Python 3.12** (or 3.9+)

### Installation Steps
1.  **Install Serverless Framework:**
    npm install -g serverless
    npm install serverless-offline --save-dev

2.  **Setup Python Environment:**
    # Navigate to the service directory
    cd ats-integration-service

    # Create virtual environment
    python3 -m venv venv
    
    # Activate environment (MacOS/Linux)
    source venv/bin/activate

    # For Windows: 
    venv\Scripts\activate

    # Install dependencies
    pip install -r requirements.txt

3.  **Configure Environment Variables:**
    Create a file named `.env` in the root of `ats-integration-service` and add your keys:
    ZOHO_CLIENT_ID=1000.xxxxxxxxx
    ZOHO_CLIENT_SECRET=xxxxxxxxxx
    ZOHO_REFRESH_TOKEN=1000.xxxxxxxxx
    ZOHO_BASE_URL=[https://recruit.zoho.in/recruit/v2](https://recruit.zoho.in/recruit/v2)

    *(Note: Never commit this file to GitHub!)*

## 🚀 4. Running the Service

Start the local serverless instance:

    serverless offline

You should see output indicating the server is ready at `http://localhost:3000`.


## 📡 5. API Usage Examples (curl) 

### A. Get All Jobs (Unified)
Returns standardized jobs with `OPEN` / `CLOSED` status.

    curl -X GET "http://localhost:3000/dev/jobs"

### B. Create Candidate (Apply)
Creates a candidate in Zoho and links them to the Job ID.

    curl -X POST "http://localhost:3000/dev/candidates" \
      -H "Content-Type: application/json" \
      -d '{
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.smith@example.com",
        "phone": "555-0100",
        "resume_url": "[https://linkedin.com/in/alicesmith](https://linkedin.com/in/alicesmith)",
        "job_id": "REPLACE_WITH_ACTUAL_JOB_ID"
      }'

### C. Get Applications
Returns applicants for a job with normalized statuses (`APPLIED`, `SCREENING`).

    curl -X GET "http://localhost:3000/dev/applications?job_id=REPLACE_WITH_ACTUAL_JOB_ID"

### D. Create New Job (Extra)
Helper endpoint to post new jobs to Zoho.

    curl -X POST "http://localhost:3000/dev/jobs" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Backend Engineer",
        "city": "Remote",
        "country": "USA",
        "remote": true,
        "description": "Building scalable APIs with Python and AWS Lambda..."
      }'
