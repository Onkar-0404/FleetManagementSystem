import os
import firebase_admin
from firebase_admin import credentials, firestore

db = None

def initialize_firebase():
    global db
    if not firebase_admin._apps:
        # 1. Check for raw JSON string in environment variable (easy for Render/cloud)
        firebase_json_env = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if firebase_json_env and firebase_json_env.strip():
            import json
            try:
                cred_dict = json.loads(firebase_json_env)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("[Firebase Init] Firebase Admin SDK initialized from FIREBASE_CREDENTIALS_JSON env var.")
                db = firestore.client()
                return db
            except Exception as e:
                print(f"[Firebase Init] Failed parsing FIREBASE_CREDENTIALS_JSON: {e}")

        # 2. Check candidate file paths
        core_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(core_dir)
        backend_dir = os.path.dirname(app_dir)

        candidate_paths = [
            os.getenv("SERVICE_ACCOUNT_PATH"),
            "/etc/secrets/service-account.json",  # Render Secret File standard path
            os.path.join(backend_dir, "service-account.json"),
            "service-account.json"
        ]

        cert_path = None
        for path in candidate_paths:
            if path and os.path.exists(path):
                cert_path = os.path.abspath(path)
                break

        if not cert_path:
            raise FileNotFoundError(
                "Firebase service account not found! Checked candidate paths:\n"
                f"{candidate_paths}\n"
                "Please add a service-account.json file or set FIREBASE_CREDENTIALS_JSON environment variable."
            )

        print(f"[Firebase Init] Resolved service-account path: '{cert_path}'")
        cred = credentials.Certificate(cert_path)
        firebase_admin.initialize_app(cred)
        print("[Firebase Init] Firebase Admin SDK initialized successfully.")
    else:
        print("[Firebase Init] Firebase Admin SDK already initialized.")

    db = firestore.client()
    return db

def get_db():
    global db
    if db is None:
        db = firestore.client()
    return db
