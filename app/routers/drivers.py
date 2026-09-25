from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import DriverUpdate, DriverResponse, AssignVehicleRequest, VehicleResponse, RegisterDriverRequest
from app.core.security import require_role, get_current_user
from app.services.firestore_service import (
    get_drivers_by_owner, get_driver_by_id, get_driver_by_user_id,
    create_user_doc, create_driver, update_driver, delete_driver,
    assign_vehicle_to_driver, get_driver_assigned_vehicle
)

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("", response_model=List[DriverResponse])
def list_drivers(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return get_drivers_by_owner(owner_id)

@router.post("/register", response_model=DriverResponse)
def register_driver(
    req: RegisterDriverRequest,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    from app.core.firebase import get_auth
    auth = get_auth()
    
    # 1. Create or retrieve Firebase Auth User for the Driver
    try:
        user_record = auth.create_user(
            email=req.email,
            password=req.password,
            display_name=req.name
        )
        user_uid = user_record.uid
    except Exception as e:
        try:
            user_record = auth.get_user_by_email(req.email)
            user_uid = user_record.uid
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create driver account: {str(e)}"
            )

    # 2. Save User Document in Firestore
    user_data = {
        "uid": user_uid,
        "email": req.email,
        "name": req.name,
        "role": "driver",
        "ownerId": owner_id,
        "phone": req.phone or ""
    }
    create_user_doc(user_uid, user_data)

    # 3. Create Driver Document in Firestore
    driver_data = {
        "name": req.name,
        "licenseNumber": req.licenseNumber,
        "phone": req.phone or "",
        "assignedVehicleId": req.assignedVehicleId,
        "status": "active"
    }
    new_driver = create_driver(owner_id, user_uid, driver_data)

    # 4. Bind vehicle if specified
    if req.assignedVehicleId:
        assign_vehicle_to_driver(owner_id, new_driver["id"], req.assignedVehicleId)
        new_driver = get_driver_by_id(new_driver["id"])

    return new_driver

@router.get("/me/vehicle", response_model=VehicleResponse)
def get_my_vehicle(current_user: dict = Depends(get_current_user)):
    user_id = current_user["uid"]
    driver = get_driver_by_user_id(user_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found"
        )
    vehicle = get_driver_assigned_vehicle(driver["id"])
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned. Please contact your fleet owner."
        )
    return vehicle

@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver_detail(
    driver_id: str,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    driver = get_driver_by_id(driver_id)
    if not driver or driver.get("ownerId") != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found or unauthorized"
        )
    return driver

@router.get("/{driver_id}/vehicle", response_model=VehicleResponse)
def get_driver_vehicle(
    driver_id: str,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    driver = get_driver_by_id(driver_id)
    if not driver or driver.get("ownerId") != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found or unauthorized"
        )
    vehicle = get_driver_assigned_vehicle(driver_id)
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No vehicle assigned to driver"
        )
    return vehicle

@router.post("/{driver_id}/assign-vehicle", response_model=DriverResponse)
def assign_vehicle(
    driver_id: str,
    payload: AssignVehicleRequest,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    updated_driver, error_msg = assign_vehicle_to_driver(owner_id, driver_id, payload.vehicleId)
    if error_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    return updated_driver

@router.delete("/{driver_id}/vehicle", response_model=DriverResponse)
def unassign_vehicle(
    driver_id: str,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    updated_driver, error_msg = assign_vehicle_to_driver(owner_id, driver_id, None)
    if error_msg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    return updated_driver

@router.put("/{driver_id}", response_model=DriverResponse)
def modify_driver(
    driver_id: str,
    driver_update: DriverUpdate,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    existing = get_driver_by_id(driver_id)
    if not existing or existing.get("ownerId") != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found or unauthorized"
        )

    if driver_update.assignedVehicleId is not None:
        target_veh = driver_update.assignedVehicleId
        updated_driver, error_msg = assign_vehicle_to_driver(owner_id, driver_id, target_veh)
        if error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

    updated = update_driver(driver_id, driver_update.model_dump())
    return updated

@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_driver(
    driver_id: str,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    existing = get_driver_by_id(driver_id)
    if not existing or existing.get("ownerId") != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found or unauthorized"
        )
    delete_driver(driver_id)
    return None
