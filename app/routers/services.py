from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import shutil
from pathlib import Path

from .. import models, schemas
from ..database import SessionLocal
from ..dependencies import get_current_user, get_current_agency, require_role

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.ServiceRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def create_service(
    service_in: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    agency_id = current_agency["id"]
    user_id = current_user["id"]

    # Check if service with the same name already exists for the agency
    existing_service = db.query(models.Service).filter(
        models.Service.agency_id == agency_id,
        models.Service.name == service_in.name
    ).first()
    if existing_service:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service with this name already exists for the agency"
        )

    service_data = service_in.dict()
    db_service = models.Service(
        **service_data,
        agency_id=agency_id,
        created_by=user_id,
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service


@router.get("/", response_model=List[schemas.ServiceRead], dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT", "CA_TEAM", "CLIENT_ADMIN", "CLIENT_USER"]))])
def list_services(
    db: Session = Depends(get_db),
    current_agency: dict = Depends(get_current_agency),
):
    agency_id = current_agency["id"]
    return db.query(models.Service).filter(models.Service.agency_id == agency_id).all()


@router.get("/{service_id}", response_model=schemas.ServiceRead, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT", "CLIENT_ADMIN", "CLIENT_USER"]))])
def get_service(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_agency: dict = Depends(get_current_agency),
):
    agency_id = current_agency["id"]
    db_service = (
        db.query(models.Service)
        .filter(models.Service.id == service_id, models.Service.agency_id == agency_id)
        .first()
    )
    if db_service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return db_service




@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def delete_service(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_agency: dict = Depends(get_current_agency),
):
    agency_id = current_agency["id"]
    db_service = (
        db.query(models.Service)
        .filter(models.Service.id == service_id, models.Service.agency_id == agency_id)
        .first()
    )
    if db_service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete(db_service)
    db.commit()
