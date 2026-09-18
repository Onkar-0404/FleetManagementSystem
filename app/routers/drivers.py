from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import DriverUpdate, DriverResponse, AssignVehicleRequest, VehicleResponse
from app.core.security import require_role, get_current_user
from app.services.firestore_service import (
    get_drivers_by_owner, get_driver_by_id, get_driver_by_user_id,
    update_driver, delete_driver, assign_vehicle_to_driver, get_driver_assigned_vehicle
)

router = APIRouter(prefix="/drivers", tags=["Drivers"])

@router.get("", response_model=List[DriverResponse])
def list_drivers(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return get_drivers_by_owner(owner_id)

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

    # If assignedVehicleId is being updated
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
