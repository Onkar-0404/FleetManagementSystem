from typing import List, Optional, Dict, Any
from app.core.firebase import get_db

# User Service
def create_user_doc(uid: str, user_data: Dict[str, Any]):
    db = get_db()
    db.collection("users").document(uid).set(user_data)
    return user_data

def get_user_doc(uid: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        data["uid"] = uid
        return data
    return None

def get_owner_by_invite_code(invite_code: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    query = db.collection("users").where("role", "==", "owner").where("inviteCode", "==", invite_code).limit(1).stream()
    for doc in query:
        data = doc.to_dict()
        data["uid"] = doc.id
        return data
    return None

# Invitation Service (Admin Invite-Only System)
def create_invitation(owner_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    data["createdBy"] = owner_id
    doc_ref = db.collection("invitations").document()
    invitation_id = doc_ref.id
    data["id"] = invitation_id
    doc_ref.set(data)
    return data

def get_invitation_by_token(token: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    query = db.collection("invitations").where("token", "==", token).limit(1).stream()
    for doc in query:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None

def get_invitations_by_owner(owner_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    query = db.collection("invitations").where("createdBy", "==", owner_id).stream()
    invitations = []
    for doc in query:
        data = doc.to_dict()
        data["id"] = doc.id
        invitations.append(data)
    return invitations

def update_invitation(invitation_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc_ref = db.collection("invitations").document(invitation_id)
    doc = doc_ref.get()
    if doc.exists:
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        if clean_updates:
            doc_ref.update(clean_updates)
        updated = doc_ref.get().to_dict()
        updated["id"] = invitation_id
        return updated
    return None

# Vehicle Service
def create_vehicle(owner_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    data["ownerId"] = owner_id
    doc_ref = db.collection("vehicles").document()
    vehicle_id = doc_ref.id
    data["id"] = vehicle_id
    doc_ref.set(data)
    return data

def get_vehicles_by_owner(owner_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    query = db.collection("vehicles").where("ownerId", "==", owner_id).stream()
    vehicles = []
    for doc in query:
        v = doc.to_dict()
        v["id"] = doc.id
        vehicles.append(v)
    return vehicles

def get_vehicle_by_id(vehicle_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("vehicles").document(vehicle_id).get()
    if doc.exists:
        v = doc.to_dict()
        v["id"] = doc.id
        return v
    return None

def update_vehicle(vehicle_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc_ref = db.collection("vehicles").document(vehicle_id)
    if doc_ref.get().exists:
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        if clean_updates:
            doc_ref.update(clean_updates)
        updated = doc_ref.get().to_dict()
        updated["id"] = vehicle_id
        return updated
    return None

def delete_vehicle(vehicle_id: str) -> bool:
    db = get_db()
    doc_ref = db.collection("vehicles").document(vehicle_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return True
    return False

# Driver Service
def create_driver(owner_id: str, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    data["ownerId"] = owner_id
    data["userId"] = user_id
    doc_ref = db.collection("drivers").document()
    driver_id = doc_ref.id
    data["id"] = driver_id
    doc_ref.set(data)
    return data

def get_drivers_by_owner(owner_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    query = db.collection("drivers").where("ownerId", "==", owner_id).stream()
    drivers = []
    for doc in query:
        d = doc.to_dict()
        d["id"] = doc.id
        drivers.append(d)
    return drivers

def get_driver_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    query = db.collection("drivers").where("userId", "==", user_id).limit(1).stream()
    for doc in query:
        d = doc.to_dict()
        d["id"] = doc.id
        return d
    return None

def get_driver_by_id(driver_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("drivers").document(driver_id).get()
    if doc.exists:
        d = doc.to_dict()
        d["id"] = doc.id
        return d
    return None

def update_driver(driver_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc_ref = db.collection("drivers").document(driver_id)
    if doc_ref.get().exists:
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        if clean_updates:
            doc_ref.update(clean_updates)
        updated = doc_ref.get().to_dict()
        updated["id"] = driver_id
        return updated
    return None

def delete_driver(driver_id: str) -> bool:
    db = get_db()
    doc_ref = db.collection("drivers").document(driver_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return True
    return False

def get_available_vehicles(owner_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    query = db.collection("vehicles").where("ownerId", "==", owner_id).stream()
    vehicles = []
    for doc in query:
        v = doc.to_dict()
        v["id"] = doc.id
        # Include all vehicles for owner with assignment metadata
        vehicles.append(v)
    return vehicles

def assign_vehicle_to_driver(owner_id: str, driver_id: str, vehicle_id: Optional[str]) -> (Optional[Dict[str, Any]], Optional[str]):
    db = get_db()
    driver_ref = db.collection("drivers").document(driver_id)
    driver_doc = driver_ref.get()
    if not driver_doc.exists:
        return None, "Driver not found"
    
    driver = driver_doc.to_dict()
    if driver.get("ownerId") != owner_id:
        return None, "Unauthorized driver access"

    old_vehicle_id = driver.get("assignedVehicleId")

    # If vehicle_id is provided and not empty
    if vehicle_id and vehicle_id.strip():
        target_veh_id = vehicle_id.strip()
        vehicle_ref = db.collection("vehicles").document(target_veh_id)
        vehicle_doc = vehicle_ref.get()

        # Fallback: Check if target_veh_id matches regNumber
        if not vehicle_doc.exists:
            query = db.collection("vehicles").where("ownerId", "==", owner_id).where("regNumber", "==", target_veh_id).limit(1).stream()
            found_doc = None
            for doc in query:
                found_doc = doc
                break
            if found_doc:
                vehicle_doc = found_doc
                target_veh_id = found_doc.id
                vehicle_ref = db.collection("vehicles").document(target_veh_id)
            else:
                return None, "Vehicle not found"

        vehicle = vehicle_doc.to_dict()
        if vehicle.get("ownerId") != owner_id:
            return None, "Unauthorized vehicle access"

        current_assigned_driver = vehicle.get("assignedDriverId")

        # If vehicle was assigned to a different driver, unassign that driver first
        if current_assigned_driver and current_assigned_driver != driver_id:
            old_driver_ref = db.collection("drivers").document(current_assigned_driver)
            if old_driver_ref.get().exists:
                old_driver_ref.update({"assignedVehicleId": None})

        # Unassign old vehicle from current driver if different
        if old_vehicle_id and old_vehicle_id != target_veh_id:
            old_veh_ref = db.collection("vehicles").document(old_vehicle_id)
            if old_veh_ref.get().exists:
                old_veh_ref.update({"assignedDriverId": None})
            else:
                q = db.collection("vehicles").where("ownerId", "==", owner_id).where("regNumber", "==", old_vehicle_id).stream()
                for doc in q:
                    doc.reference.update({"assignedDriverId": None})

        # Assign new vehicle to driver and driver to vehicle
        vehicle_ref.update({"assignedDriverId": driver_id})
        driver_ref.update({"assignedVehicleId": target_veh_id})
    else:
        # Unassign current vehicle
        if old_vehicle_id:
            old_veh_ref = db.collection("vehicles").document(old_vehicle_id)
            if old_veh_ref.get().exists:
                old_veh_ref.update({"assignedDriverId": None})
            else:
                q = db.collection("vehicles").where("ownerId", "==", owner_id).where("regNumber", "==", old_vehicle_id).stream()
                for doc in q:
                    doc.reference.update({"assignedDriverId": None})
        driver_ref.update({"assignedVehicleId": None})

    updated_driver = driver_ref.get().to_dict()
    updated_driver["id"] = driver_id
    return updated_driver, None

def get_driver_assigned_vehicle(driver_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    driver_doc = db.collection("drivers").document(driver_id).get()
    if driver_doc.exists:
        driver = driver_doc.to_dict()
        vehicle_id = driver.get("assignedVehicleId")
        if vehicle_id:
            vehicle_doc = db.collection("vehicles").document(vehicle_id).get()
            if vehicle_doc.exists:
                v = vehicle_doc.to_dict()
                v["id"] = vehicle_doc.id
                return v
            # Fallback by regNumber
            query = db.collection("vehicles").where("regNumber", "==", vehicle_id).limit(1).stream()
            for doc in query:
                v = doc.to_dict()
                v["id"] = doc.id
                return v
    return None


# Trip Service
def calculate_trip_financials(trip_data: Dict[str, Any]) -> None:
    rate = trip_data.get("rate")
    rate_type = trip_data.get("rateType", "per_weight")
    weight = trip_data.get("materialWeight")

    earnings = None
    if rate is not None:
        try:
            rate_val = float(rate)
            if rate_type == "per_weight":
                if weight is not None:
                    earnings = round(rate_val * float(weight), 2)
            elif rate_type == "flat":
                earnings = round(rate_val, 2)
        except (ValueError, TypeError):
            earnings = None
    elif trip_data.get("earnings") is not None:
        try:
            earnings = round(float(trip_data.get("earnings")), 2)
        except (ValueError, TypeError):
            earnings = None

    fuel_val = trip_data.get("fuelCost")
    fuel = float(fuel_val) if fuel_val is not None else 0.0
    toll = float(trip_data.get("tollAmount", 0.0) or 0.0)
    loading = float(trip_data.get("loadingUnloadingAmount", 0.0) or 0.0)
    other = float(trip_data.get("otherExpenses", 0.0) or 0.0)

    total_cost = round(fuel + toll + loading + other, 2)

    profit = None
    if earnings is not None:
        profit = round(earnings - total_cost, 2)

    trip_data["earnings"] = earnings
    trip_data["profit"] = profit

def create_trip(owner_id: str, driver_id: str, trip_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    trip_data["ownerId"] = owner_id
    trip_data["driverId"] = driver_id
    
    calculate_trip_financials(trip_data)
    
    doc_ref = db.collection("trips").document()
    trip_id = doc_ref.id
    trip_data["id"] = trip_id
    doc_ref.set(trip_data)
    return trip_data

def get_trip_by_id(trip_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.collection("trips").document(trip_id).get()
    if doc.exists:
        t = doc.to_dict()
        t["id"] = doc.id
        return t
    return None

def update_trip(trip_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc_ref = db.collection("trips").document(trip_id)
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        clean_updates = {k: v for k, v in updates.items() if v is not None}
        if clean_updates:
            merged = {**data, **clean_updates}
            calculate_trip_financials(merged)
            clean_updates["earnings"] = merged.get("earnings")
            clean_updates["profit"] = merged.get("profit")
            doc_ref.update(clean_updates)
        updated = doc_ref.get().to_dict()
        updated["id"] = trip_id
        return updated
    return None

def delete_trip(trip_id: str) -> bool:
    db = get_db()
    doc_ref = db.collection("trips").document(trip_id)
    if doc_ref.get().exists:
        doc_ref.delete()
        return True
    return False


def get_trips_by_owner(owner_id: str, date: Optional[str] = None, driver_id: Optional[str] = None, vehicle_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_db()
    query = db.collection("trips").where("ownerId", "==", owner_id)
    
    if date:
        query = query.where("date", "==", date)
    if driver_id:
        query = query.where("driverId", "==", driver_id)
    if vehicle_id:
        query = query.where("vehicleId", "==", vehicle_id)
        
    stream = query.stream()
    trips = []
    for doc in stream:
        t = doc.to_dict()
        t["id"] = doc.id
        trips.append(t)
    return trips

def get_trips_by_driver(driver_id: str) -> List[Dict[str, Any]]:
    db = get_db()
    stream = db.collection("trips").where("driverId", "==", driver_id).stream()
    trips = []
    for doc in stream:
        t = doc.to_dict()
        t["id"] = doc.id
        trips.append(t)
    return trips
