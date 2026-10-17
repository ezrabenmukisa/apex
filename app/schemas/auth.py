import uuid
from pydantic import BaseModel, Field

class FirebaseAuthRequest(BaseModel):
    id_token: str = Field(..., description="Firebase ID token received from the Frontend Client")

class FirebaseAuthResponse(BaseModel):
    user_id: uuid.UUID 
    profile_complete: bool