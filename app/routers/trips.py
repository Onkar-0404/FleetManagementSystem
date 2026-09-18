import io
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from PIL import Image

from app.models.schemas import TripCreate, TripUpdate, TripResponse
from app.core.security import get_current_user, require_role, log_security_event
from app.services.firestore_service import (
    create_trip, get_trips_by_owner, get_trips_by_driver, get_driver_by_user_id,
    get_trip_by_id, update_trip
)

router = APIRouter(prefix="/trips", tags=["Trips"])

# Storage directory for uploaded fuel receipts outside public web root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RECEIPTS_DIR = os.path.join(BASE_DIR, "receipts_storage")
os.makedirs(RECEIPTS_DIR, exist_ok=True)

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit

def validate_magic_bytes(data: bytes) -> bool:
    """Validate file binary magic bytes (JPEG, PNG, WebP)."""
    if len(data) < 4:
        return False
    if data.startswith(b"\xFF\xD8\xFF"):
        return True  # JPEG
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return True  # PNG
    if len(data) >= 12 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return True  # WebP
    return False

@router.post("/upload-receipt")
async def upload_receipt(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    uid = current_user["uid"]
    
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_BYTES:
        log_security_event("UPLOAD_SIZE_EXCEEDED", uid, f"Attempted upload size: {len(content)} bytes")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed limit of 5 MB."
        )
        
    if not validate_magic_bytes(content):
        log_security_event("MAGIC_BYTES_VALIDATION_FAILED", uid, f"Filename: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format. Only JPEG, PNG, and WebP files are accepted."
        )
        
    try:
        # Re-encode image with Pillow to strip EXIF metadata, camera tags, and potential polyglots
        input_image = Image.open(io.BytesIO(content))
        rgb_image = input_image.convert("RGB")
        
        output_buffer = io.BytesIO()
        rgb_image.save(output_buffer, format="JPEG", quality=85)
        clean_bytes = output_buffer.getvalue()
        
        filename = f"{uuid.uuid4().hex}.jpg"
        file_path = os.path.join(RECEIPTS_DIR, filename)
        
        with open(file_path, "wb") as f:
            f.write(clean_bytes)
            
        log_security_event("RECEIPT_UPLOAD_SUCCESS", uid, f"Saved receipt file {filename}")
        return {"receiptUrl": f"/trips/receipt/{filename}", "filename": filename}
    except Exception as e:
        log_security_event("RECEIPT_PROCESSING_FAILED", uid, f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process receipt image: {str(e)}"
        )

@router.get("/receipt/{filename}")
def serve_receipt_file(
    filename: str,
    current_user: dict = Depends(get_current_user)
):
    """Auth-gated receipt file retrieval."""
    safe_filename = os.path.basename(filename)
    file_path = os.path.join(RECEIPTS_DIR, safe_filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Receipt photo not found")
        
    return FileResponse(file_path, media_type="image/jpeg")

@router.get("/{trip_id}/receipt")
def get_trip_receipt_bola_gated(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    """BOLA / BFLA Gated Endpoint for retrieving trip fuel receipt."""
    uid = current_user["uid"]
    role = current_user.get("role")
    
    trip = get_trip_by_id(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Enforce Server-Side Ownership Verification (BOLA/BFLA)
    has_access = False
    if role == "owner":
        if trip.get("ownerId") == uid:
            has_access = True
    elif role == "driver":
        driver_doc = get_driver_by_user_id(uid)
        if driver_doc and trip.get("driverId") == driver_doc.get("id"):
            has_access = True
            
    if not has_access:
        log_security_event(
            "BOLA_UNAUTHORIZED_RECEIPT_ACCESS",
            uid,
            f"User with role '{role}' attempted to view receipt for trip '{trip_id}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this trip's receipt."
        )
        
    receipt_url = trip.get("receiptUrl")
    if not receipt_url:
        raise HTTPException(status_code=404, detail="No fuel receipt attached to this trip")
        
    # Extract filename from receiptUrl (e.g., /trips/receipt/{filename})
    filename = os.path.basename(receipt_url)
    file_path = os.path.join(RECEIPTS_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Receipt file not found on server")
        
    return FileResponse(file_path, media_type="image/jpeg")

@router.post("", response_model=TripResponse)
def log_trip(
    req: TripCreate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["uid"]
    role = current_user.get("role")
    
    if role == "driver":
        driver_doc = get_driver_by_user_id(user_id)
        if not driver_doc:
            raise HTTPException(status_code=400, detail="Driver record not found")
        driver_id = driver_doc["id"]
        owner_id = driver_doc["ownerId"]
    elif role == "owner":
        owner_id = user_id
        driver_id = "owner_log"
    else:
        raise HTTPException(status_code=403, detail="Unauthorized role")
        
    created = create_trip(owner_id, driver_id, req.dict())
    log_security_event("TRIP_CREATED", user_id, f"Trip {created.get('id')} logged successfully")
    return created

@router.put("/{trip_id}", response_model=TripResponse)
def update_trip_endpoint(
    trip_id: str,
    req: TripUpdate,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    existing = get_trip_by_id(trip_id)
    if not existing or existing.get("ownerId") != owner_id:
        log_security_event("BOLA_UNAUTHORIZED_TRIP_UPDATE", owner_id, f"Attempted to update trip {trip_id}")
        raise HTTPException(status_code=404, detail="Trip not found or unauthorized")
        
    updated = update_trip(trip_id, req.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update trip")
    log_security_event("TRIP_UPDATED", owner_id, f"Trip {trip_id} updated successfully")
    return updated

@router.get("/me", response_model=List[TripResponse])
def get_my_trips(current_user: dict = Depends(get_current_user)):
    user_id = current_user["uid"]
    role = current_user.get("role")
    
    if role == "driver":
        driver_doc = get_driver_by_user_id(user_id)
        if not driver_doc:
            return []
        return get_trips_by_driver(driver_doc["id"])
    elif role == "owner":
        return get_trips_by_owner(user_id)
    return []

@router.get("", response_model=List[TripResponse])
def get_all_trips(
    date: Optional[str] = None,
    driverId: Optional[str] = None,
    vehicleId: Optional[str] = None,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    return get_trips_by_owner(owner_id, date, driverId, vehicleId)

