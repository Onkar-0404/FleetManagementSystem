from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import VehicleCreate, VehicleUpdate, VehicleResponse
from app.core.security import require_role
from app.services.firestore_service import (
    create_vehicle, get_vehicles_by_owner, get_vehicle_by_id, update_vehicle, delete_vehicle, get_available_vehicles
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.get("", response_model=List[VehicleResponse])
def list_vehicles(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return get_vehicles_by_owner(owner_id)

@router.get("/available", response_model=List[VehicleResponse])
def list_available_vehicles(current_user: dict = Depends(require_role("owner"))):
    owner_id = current_user["uid"]
    return get_available_vehicles(owner_id)

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def add_vehicle(
    vehicle: VehicleCreate,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    return create_vehicle(owner_id, vehicle.model_dump())

@router.put("/{vehicle_id}", response_model=VehicleResponse)
def modify_vehicle(
    vehicle_id: str,
    vehicle_update: VehicleUpdate,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    existing = get_vehicle_by_id(vehicle_id)
    if not existing or existing.get("ownerId") != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found or unauthorized"
        )

    # Import assignment helper to sync driver doc if assignedDriverId is modified
    if vehicle_update.assignedDriverId is not None:
        target_driver = vehicle_update.assignedDriverId
        if target_driver and target_driver.strip():
            from app.services.firestore_service import assign_vehicle_to_driver
            _, error_msg = assign_vehicle_to_driver(owner_id, target_driver, vehicle_id)
            if error_msg:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

    updated = update_vehicle(vehicle_id, vehicle_update.model_dump())
    return updated


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_vehicle(
    vehicle_id: str,
    current_user: dict = Depends(require_role("owner"))
):
    owner_id = current_user["uid"]
    existing = get_vehicle_by_id(vehicle_id)
    if not existing or existing.get("ownerId") != owner_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found or unauthorized"
        )
    delete_vehicle(vehicle_id)
    return None
