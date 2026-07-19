import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

db = None
bucket = None
app = None

try:
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        raise ValueError("FIREBASE_PROJECT_ID not set")

    # Use REST API instead of credentials for Vercel
    from google.cloud import firestore as fs
    from google.cloud import storage as st
    from google.oauth2 import service_account

    # Get credentials from environment
    creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")

    if creds_json:
        # Use explicit credentials if provided
        import json
        creds_dict = json.loads(creds_json)
        credentials_obj = service_account.Credentials.from_service_account_info(creds_dict)
    else:
        # Use default app credentials (for Vercel)
        credentials_obj = None

    # Initialize Firestore
    db = fs.Client(project=project_id, credentials=credentials_obj)

    # Initialize Storage
    try:
        storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
        bucket = st.Client(project=project_id, credentials=credentials_obj).bucket(storage_bucket_name)
    except Exception as e:
        print(f"Warning: Storage bucket init failed: {e}")
        bucket = None

except Exception as e:
    print(f"Firebase initialization warning: {e}")
    print("App will use demo mode - no persistence")
    db = None
    bucket = None
