from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import routers

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

app.include_router(routers.services.router, prefix="/services", tags=["services"])
app.include_router(routers.options.router, prefix="/options", tags=["options"])
app.include_router(routers.clients.router, prefix="/clients", tags=["clients"])
