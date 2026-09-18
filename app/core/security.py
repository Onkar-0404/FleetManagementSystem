from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from app.core.firebase import get_db

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    try:
        decoded_token = auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    uid = decoded_token.get("uid")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing uid claim",
        )
        
    db = get_db()
    user_doc = db.collection("users").document(uid).get()
    
    if not user_doc.exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User profile not found for UID {uid}",
        )
        
    user_data = user_doc.to_dict()
    user_data["uid"] = uid
    return user_data

def require_role(required_role: str):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role != required_role:
            log_security_event("BFLA_ROLE_VIOLATION", current_user.get("uid", "unknown"), f"Required {required_role}, but user has {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Requires role '{required_role}', but current user has role '{user_role}'.",
            )
        return current_user
    return role_checker

import logging
import datetime

logger = logging.getLogger("security_audit")
logger.setLevel(logging.INFO)

def log_security_event(event_type: str, uid: str, detail: str):
    """
    Log security events without sensitive token/password data.
    """
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    safe_detail = detail.replace("\n", " ").replace("\r", " ")
    print(f"[SECURITY_AUDIT] [{timestamp}] event={event_type} uid={uid} detail={safe_detail}")
    logger.info(f"event={event_type} uid={uid} detail={safe_detail}")

