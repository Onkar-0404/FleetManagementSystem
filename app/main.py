from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.firebase import initialize_firebase
from app.routers import auth, vehicles, drivers, trips, reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=== Starting Fleet Management Backend Application ===")
    initialize_firebase()
    yield
    print("=== Shutting Down Fleet Management Backend Application ===")

import os

env = os.getenv("ENV", "development").lower()
is_prod = env == "production"

app = FastAPI(
    title="Fleet Management API",
    description="Backend REST API for Fleet Management App (Firebase Auth & Firestore)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if is_prod else "/docs",
    redoc_url=None if is_prod else "/redoc",
)


# Enable CORS for device/emulator access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(vehicles.router)
app.include_router(drivers.router)
app.include_router(trips.router)
app.include_router(reports.router)

@app.get("/", tags=["Health"])
def root_health_check():
    return {"status": "ok", "message": "Fleet Management API is running"}

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "fleet-backend"}
