from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr

# Auth Schemas
class RegisterOwnerRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class RegisterDriverRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    licenseNumber: str
    assignedVehicleId: Optional[str] = None

class RegisterDriverSelfRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    licenseNumber: str
    ownerInviteCode: str

class UserResponse(BaseModel):
    uid: str
    role: str
    name: str
    email: str
    ownerId: Optional[str] = None
    phone: Optional[str] = None
    inviteCode: Optional[str] = None

# Invitation Schemas (Admin Invite-Only System)
class CreateInvitationRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "driver"
    phone: Optional[str] = None
    licenseNumber: Optional[str] = None

class ValidateInvitationRequest(BaseModel):
    token: str

class InvitationDetailResponse(BaseModel):
    token: str
    email: str
    role: str
    status: str
    name: str
    phone: Optional[str] = None
    licenseNumber: Optional[str] = None
    expiresAt: str

class RegisterWithInvitationRequest(BaseModel):
    token: str
    password: str
    name: Optional[str] = None

class InvitationResponse(BaseModel):
    id: str
    token: str
    email: str
    role: str
    createdBy: str
    createdAt: str
    expiresAt: str
    status: str
    usedAt: Optional[str] = None
    name: str
    phone: Optional[str] = None
    licenseNumber: Optional[str] = None

# Vehicle Schemas
class VehicleCreate(BaseModel):
    regNumber: str
    model: str
    type: str
    assignedDriverId: Optional[str] = None
    status: str = "active"

class VehicleUpdate(BaseModel):
    regNumber: Optional[str] = None
    model: Optional[str] = None
    type: Optional[str] = None
    assignedDriverId: Optional[str] = None
    status: Optional[str] = None

class VehicleResponse(BaseModel):
    id: str
    ownerId: str
    regNumber: str
    model: str
    type: str
    assignedDriverId: Optional[str] = None
    status: str

# Driver Schemas
class DriverUpdate(BaseModel):
    name: Optional[str] = None
    licenseNumber: Optional[str] = None
    phone: Optional[str] = None
    assignedVehicleId: Optional[str] = None
    status: Optional[str] = None

class AssignVehicleRequest(BaseModel):
    vehicleId: Optional[str] = None


class DriverResponse(BaseModel):
    id: str
    ownerId: str
    userId: str
    name: str
    licenseNumber: str
    phone: Optional[str] = None
    assignedVehicleId: Optional[str] = None
    status: str

# Trip Schemas
class TripCreate(BaseModel):
    vehicleId: str
    date: str  # YYYY-MM-DD
    startLocation: str
    endLocation: str
    distanceKm: Optional[float] = Field(default=None, ge=0, description="Optional distance for backward compatibility")
    fuelCost: Optional[float] = Field(default=None, ge=0, description="Fuel cost is optional")
    materialWeight: Optional[float] = Field(default=None, gt=0, description="Material cargo weight in tons")
    loadingUnloadingAmount: float = Field(default=0.0, ge=0, description="Loading / unloading site charges")
    tollAmount: float = Field(default=0.0, ge=0, description="Toll plaza charges")
    otherExpenses: float = Field(default=0.0, ge=0, description="Other expenses must be non-negative")
    rate: Optional[float] = Field(default=None, ge=0, description="Agreed freight rate (owner only)")
    rateType: Optional[str] = Field(default="per_weight", description="per_weight or flat")
    earnings: Optional[float] = Field(default=None, description="Earnings optional at creation")
    notes: Optional[str] = None
    receiptUrl: Optional[str] = None

class TripUpdate(BaseModel):
    vehicleId: Optional[str] = None
    date: Optional[str] = None
    startLocation: Optional[str] = None
    endLocation: Optional[str] = None
    distanceKm: Optional[float] = None
    fuelCost: Optional[float] = None
    materialWeight: Optional[float] = None
    loadingUnloadingAmount: Optional[float] = None
    tollAmount: Optional[float] = None
    otherExpenses: Optional[float] = None
    rate: Optional[float] = None
    rateType: Optional[str] = None
    earnings: Optional[float] = None
    notes: Optional[str] = None
    receiptUrl: Optional[str] = None

class TripResponse(BaseModel):
    id: str
    ownerId: str
    driverId: str
    vehicleId: str
    date: str
    startLocation: str
    endLocation: str
    distanceKm: Optional[float] = None
    fuelCost: Optional[float] = None
    materialWeight: Optional[float] = None
    loadingUnloadingAmount: float = 0.0
    tollAmount: float = 0.0
    otherExpenses: float = 0.0
    rate: Optional[float] = None
    rateType: Optional[str] = None
    earnings: Optional[float] = None
    profit: Optional[float] = None
    notes: Optional[str] = None
    receiptUrl: Optional[str] = None


# Report Schemas
class DailyReportItem(BaseModel):
    date: str
    totalTrips: int
    totalDistanceKm: float = 0.0
    totalEarnings: float
    totalFuelCost: float
    totalTollAmount: float = 0.0
    totalLoadingUnloadingAmount: float = 0.0
    totalOtherExpenses: float
    netProfit: float

class DailyReportResponse(BaseModel):
    items: List[DailyReportItem]
    grandTotalEarnings: float
    grandTotalFuelCost: float
    grandTotalExpenses: float
    grandTotalProfit: float

class MonthlyReportItem(BaseModel):
    month: str  # YYYY-MM
    totalTrips: int
    totalDistanceKm: float = 0.0
    totalEarnings: float
    totalFuelCost: float
    totalTollAmount: float = 0.0
    totalLoadingUnloadingAmount: float = 0.0
    totalOtherExpenses: float
    netProfit: float

class MonthlyReportResponse(BaseModel):
    items: List[MonthlyReportItem]
    grandTotalEarnings: float
    grandTotalFuelCost: float
    grandTotalExpenses: float
    grandTotalProfit: float

class ProfitReportResponse(BaseModel):
    totalTrips: int
    totalDistanceKm: float = 0.0
    totalEarnings: float
    totalFuelCost: float
    totalTollAmount: float = 0.0
    totalLoadingUnloadingAmount: float = 0.0
    totalOtherExpenses: float
    netProfit: float
    profitMarginPercent: float
    totalVehicles: int = 0
    activeDrivers: int = 0
    tripsToday: int = 0
