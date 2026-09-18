import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, status
from firebase_admin import auth as firebase_auth

from app.models.schemas import (
    RegisterOwnerRequest, RegisterDriverRequest, RegisterDriverSelfRequest, UserResponse,
    CreateInvitationRequest, ValidateInvitationRequest, RegisterWithInvitationRequest,
    InvitationResponse, InvitationDetailResponse
)
from app.services.firestore_service import (
    create_user_doc, get_user_doc, get_owner_by_invite_code, create_driver,
    create_invitation, get_invitation_by_token, get_invitations_by_owner, update_invitation
)
from app.core.security import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication & Invitations"])

# Block Unrestricted Public Signups (Strict Security Requirement)
@router.post("/register-owner", response_model=UserResponse)
def register_owner(req: RegisterOwnerRequest):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public owner signup is disabled. Accounts can only be created via an invitation from an administrator."
    )

@router.post("/register-driver-self", response_model=UserResponse)
def register_driver_self(req: RegisterDriverSelfRequest):
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Public driver signup is disabled. Account creation requires a valid invitation from an administrator."
    )

# Admin Invite-Only System Endpoints
@router.post("/invitations", response_model=InvitationResponse)
def create_invitation_endpoint(
    req: CreateInvitationRequest,
    current_user: Dict[str, Any] = Depends(require_role("owner"))
):
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=48)

    invitation_data = {
        "token": token,
        "email": req.email.lower().strip(),
        "name": req.name.strip(),
        "role": req.role.lower().strip(),
        "phone": req.phone,
        "licenseNumber": req.licenseNumber,
        "createdAt": now.isoformat(),
        "expiresAt": expires_at.isoformat(),
        "status": "pending",
        "usedAt": None
    }

    created = create_invitation(current_user["uid"], invitation_data)
    return created

@router.get("/invitations", response_model=List[InvitationResponse])
def list_invitations_endpoint(
    current_user: Dict[str, Any] = Depends(require_role("owner"))
):
    invitations = get_invitations_by_owner(current_user["uid"])
    return invitations

@router.post("/invitations/cancel/{invitation_id}", response_model=InvitationResponse)
def cancel_invitation_endpoint(
    invitation_id: str,
    current_user: Dict[str, Any] = Depends(require_role("owner"))
):
    updated = update_invitation(invitation_id, {"status": "cancelled"})
    if not updated:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return updated

@router.post("/invitations/validate", response_model=InvitationDetailResponse)
def validate_invitation_endpoint(req: ValidateInvitationRequest):
    token = req.token.strip()
    invitation = get_invitation_by_token(token)

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This invitation is invalid.")

    if invitation.get("status") == "used":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has already been used.")

    if invitation.get("status") == "cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has been cancelled.")

    expires_at_str = invitation.get("expiresAt")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) > expires_at:
            update_invitation(invitation["id"], {"status": "expired"})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired. Please contact the administrator.")

    return InvitationDetailResponse(
        token=invitation["token"],
        email=invitation["email"],
        role=invitation["role"],
        status=invitation["status"],
        name=invitation["name"],
        phone=invitation.get("phone"),
        licenseNumber=invitation.get("licenseNumber"),
        expiresAt=invitation["expiresAt"]
    )

@router.post("/register-with-invitation", response_model=UserResponse)
def register_with_invitation(req: RegisterWithInvitationRequest):
    token = req.token.strip()
    invitation = get_invitation_by_token(token)

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This invitation is invalid.")

    if invitation.get("status") == "used":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has already been used.")

    if invitation.get("status") == "cancelled":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has been cancelled.")

    expires_at_str = invitation.get("expiresAt")
    if expires_at_str:
        expires_at = datetime.fromisoformat(expires_at_str)
        if datetime.now(timezone.utc) > expires_at:
            update_invitation(invitation["id"], {"status": "expired"})
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This invitation has expired. Please contact the administrator.")

    email = invitation["email"].lower().strip()
    role = invitation["role"]  # STRICT SERVER-SIDE ROLE ASSIGNMENT
    owner_id = invitation["createdBy"]
    name = req.name.strip() if req.name and req.name.strip() else invitation.get("name", "User")

    # Create Firebase Auth user
    try:
        fb_user = firebase_auth.create_user(
            email=email,
            password=req.password,
            display_name=name
        )
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An account with this email address already exists.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Firebase user creation failed: {str(e)}")

    uid = fb_user.uid

    user_data = {
        "uid": uid,
        "role": role,
        "name": name,
        "email": email,
        "ownerId": owner_id if role == "driver" else None,
        "phone": invitation.get("phone")
    }

    create_user_doc(uid, user_data)

    if role == "driver":
        driver_data = {
            "name": name,
            "licenseNumber": invitation.get("licenseNumber", "PENDING"),
            "phone": invitation.get("phone"),
            "assignedVehicleId": None,
            "status": "active"
        }
        create_driver(owner_id=owner_id, user_id=uid, data=driver_data)

    # Mark invitation as USED
    update_invitation(invitation["id"], {
        "status": "used",
        "usedAt": datetime.now(timezone.utc).isoformat()
    })

    return UserResponse(
        uid=uid,
        role=role,
        name=name,
        email=email,
        ownerId=owner_id if role == "driver" else None,
        phone=invitation.get("phone")
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_doc = get_user_doc(current_user["uid"])
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")
    return user_doc
