import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

firebase_config = {
    "type": "service_account",
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": "key-id",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQE\n-----END PRIVATE KEY-----\n",
    "client_email": f"firebase-adminsdk@{os.getenv('FIREBASE_PROJECT_ID')}.iam.gserviceaccount.com",
    "client_id": "123456789",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
}

try:
    app = firebase_admin.initialize_app(
        credentials.Certificate(firebase_config),
        {"storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")}
    )
except:
    app = firebase_admin.get_app()

db = firestore.client()
bucket = storage.bucket()
