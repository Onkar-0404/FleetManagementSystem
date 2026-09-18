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
        vehicle_ref = db.collection("vehicles").document(vehicle_id)
        vehicle_doc = vehicle_ref.get()
        if not vehicle_doc.exists:
            return None, "Vehicle not found"
        
        vehicle = vehicle_doc.to_dict()
        if vehicle.get("ownerId") != owner_id:
            return None, "Unauthorized vehicle access"
        
        # Check if vehicle is assigned to another driver
        current_assigned_driver = vehicle.get("assignedDriverId")
        if current_assigned_driver and current_assigned_driver != driver_id:
            return None, "Vehicle already assigned to another driver."
        
        # Unassign old vehicle if different
        if old_vehicle_id and old_vehicle_id != vehicle_id:
            db.collection("vehicles").document(old_vehicle_id).update({"assignedDriverId": None})
        
        # Assign new vehicle
        vehicle_ref.update({"assignedDriverId": driver_id})
        driver_ref.update({"assignedVehicleId": vehicle_id})
    else:
        # Unassign current vehicle
        if old_vehicle_id:
            db.collection("vehicles").document(old_vehicle_id).update({"assignedDriverId": None})
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
    return None


# Trip Service
def create_trip(owner_id: str, driver_id: str, trip_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    trip_data["ownerId"] = owner_id
    trip_data["driverId"] = driver_id
    
    earnings = trip_data.get("earnings")
    if earnings is not None:
        earnings = float(earnings)
        fuel = float(trip_data.get("fuelCost", 0.0))
        other = float(trip_data.get("otherExpenses", 0.0))
        trip_data["earnings"] = earnings
        trip_data["profit"] = earnings - fuel - other
    else:
        trip_data["earnings"] = None
        trip_data["profit"] = None
    
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
            earnings = clean_updates.get("earnings", data.get("earnings"))
            if earnings is not None:
                earnings = float(earnings)
                fuel = float(clean_updates.get("fuelCost", data.get("fuelCost", 0.0)))
                other = float(clean_updates.get("otherExpenses", data.get("otherExpenses", 0.0)))
                clean_updates["earnings"] = earnings
                clean_updates["profit"] = earnings - fuel - other
            doc_ref.update(clean_updates)
        updated = doc_ref.get().to_dict()
        updated["id"] = trip_id
        return updated
    return None


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
