from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import routers
from .schemas import ServiceRead, ChecklistItem
from .database import SessionLocal

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Your frontend's URL for local development
    "http://app.caconnect.synoptek.com",  # Replace with your actual frontend URL
    "https://app.datainvestigo.com",  # For HTTPS
    "https://login-api.datainvestigo.com",
    "*",
    "http://localhost:8081",
    "http://localhost:8080"
    "https://domain-api.datainvestigo.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    request.state.db = SessionLocal()
    response = await call_next(request)
    request.state.db.close()
    return response

app.include_router(routers.services.router, prefix="/services", tags=["services"])
app.include_router(routers.options.router, prefix="/options", tags=["options"])
app.include_router(routers.clients.router, prefix="/clients", tags=["clients"])
