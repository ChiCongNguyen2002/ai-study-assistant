import os
from dotenv import load_dotenv

load_dotenv('.env.local')

db = None
bucket = None

# Try to initialize Firebase, but don't crash if it fails
try:
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        print("Warning: FIREBASE_PROJECT_ID not set - running in demo mode")
    else:
        try:
            from google.cloud import firestore as fs
            from google.cloud import storage as st

            # Try to use credentials if provided
            creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
            credentials_obj = None

            if creds_json:
                import json
                from google.oauth2 import service_account
                creds_dict = json.loads(creds_json)
                credentials_obj = service_account.Credentials.from_service_account_info(creds_dict)

            # Initialize Firestore
            db = fs.Client(project=project_id, credentials=credentials_obj)

            # Initialize Storage
            try:
                storage_bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET")
                if storage_bucket_name:
                    bucket = st.Client(project=project_id, credentials=credentials_obj).bucket(storage_bucket_name)
            except Exception as e:
                print(f"Warning: Storage not available: {e}")
                bucket = None

        except Exception as e:
            print(f"Warning: Firebase not available: {e}")
            print("App will run in demo mode - uploads won't be persisted")
            db = None
            bucket = None

except Exception as e:
    print(f"Init error: {e}")
    db = None
    bucket = None
