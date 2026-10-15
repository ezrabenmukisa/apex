from firebase_admin import auth

def verify_firebase_token(id_token: str) -> dict:
    """
    Verifies a Firebase ID Token and returns claims.
    Permits up to 5 seconds clock-skew tolerance.
    """
    return auth.verify_id_token(id_token, clock_skew_seconds=5)