from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

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

@router.get("/{service_id}/count", response_model=int, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def get_client_count_for_service(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    count = db.query(models.ClientService).filter(models.ClientService.service_id == service_id).count()
    return count
