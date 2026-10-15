import os
import json
import firebase_admin
from firebase_admin import credentials
from app.config import get_settings

settings = get_settings()

def initialize_firebase():
    if firebase_admin._apps:
        return  # Already initialized

    cred_input = settings.firebase_credentials

    # Case 1: Local file path (e.g., app/core/serviceAccountKey.json)
    if isinstance(cred_input, str) and os.path.exists(cred_input):
        cred = credentials.Certificate(cred_input)

    # Case 2: Production raw JSON string in environment variable
    else:
        try:
            cred_dict = json.loads(cred_input)
            cred = credentials.Certificate(cred_dict)
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Firebase credentials from path or JSON string: {e}"
            )

    firebase_admin.initialize_app(cred)

# Boot initialize on module import
initialize_firebase()