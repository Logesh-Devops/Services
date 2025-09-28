from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import boto3

from .. import models, schemas
from ..database import SessionLocal
from ..dependencies import get_current_user, get_current_agency, require_role
from .. import config

router = APIRouter()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.patch("/settings/{service_id}", response_model=schemas.ServiceRead, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def update_service_settings(
    service_id: uuid.UUID,
    name: str = Form(None),
    is_enabled: bool = Form(None),
    is_checklist_completion_required: bool = Form(None),
    is_recurring: bool = Form(None),
    auto_task_creation_frequency: schemas.AutoTaskCreationFrequency = Form(None),
    target_date_creation_date: int = Form(None),
    assign_auto_tasks_to_users_of_respective_clients: bool = Form(None),
    assign_auto_tasks_to_users: str = Form(""),
    billing_sac_code: str = Form(None),
    billing_gst_percent: float = Form(None),
    billing_default_rate: float = Form(None),
    billing_default_billable: bool = Form(None),
    create_document_collection_request_automatically: bool = Form(None),
    document_request_default_message: str = Form(None),
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

    update_data = {
        "name": name,
        "is_enabled": is_enabled,
        "is_checklist_completion_required": is_checklist_completion_required,
        "is_recurring": is_recurring,
        "auto_task_creation_frequency": auto_task_creation_frequency,
        "target_date_creation_date": target_date_creation_date,
        "assign_auto_tasks_to_users_of_respective_clients": assign_auto_tasks_to_users_of_respective_clients,
        "assign_auto_tasks_to_users": [uuid.UUID(user_id) for user_id in assign_auto_tasks_to_users.split(",")] if assign_auto_tasks_to_users else [],
        "billing_sac_code": billing_sac_code,
        "billing_gst_percent": billing_gst_percent,
        "billing_default_rate": billing_default_rate,
        "billing_default_billable": billing_default_billable,
        "create_document_collection_request_automatically": create_document_collection_request_automatically,
        "document_request_default_message": document_request_default_message,
    }

    for key, value in update_data.items():
        if value is not None:
            setattr(db_service, key, value)

    db.commit()
    db.refresh(db_service)
    return db_service

@router.post("/checklists/{service_id}", response_model=schemas.ChecklistItem, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def create_checklist_item(
    service_id: uuid.UUID,
    checklist_item_in: schemas.ChecklistItemCreate,
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

    db_checklist_item = models.ServiceChecklist(
        **checklist_item_in.dict(), service_id=service_id
    )
    db.add(db_checklist_item)
    db.commit()
    db.refresh(db_checklist_item)
    return db_checklist_item

@router.get("/checklists/{service_id}", response_model=List[schemas.ChecklistItem], dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def get_checklist_items(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    checklist_items = db.query(models.ServiceChecklist).filter(models.ServiceChecklist.service_id == service_id).all()
    return checklist_items

@router.delete("/checklists/{checklist_item_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def delete_checklist_item(
    checklist_item_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_checklist_item = db.query(models.ServiceChecklist).filter(models.ServiceChecklist.id == checklist_item_id).first()
    if db_checklist_item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    db.delete(db_checklist_item)
    db.commit()


@router.patch("/checklists/{checklist_item_id}", response_model=schemas.ChecklistItem, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def update_checklist_item(
    checklist_item_id: uuid.UUID,
    checklist_item_in: schemas.ChecklistItemUpdate,
    db: Session = Depends(get_db),
):
    db_checklist_item = db.query(models.ServiceChecklist).filter(models.ServiceChecklist.id == checklist_item_id).first()
    if db_checklist_item is None:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    update_data = checklist_item_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_checklist_item, key, value)

    db.commit()
    db.refresh(db_checklist_item)
    return db_checklist_item

@router.post("/subtasks/{service_id}", response_model=schemas.Subtask, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def create_subtask(
    service_id: uuid.UUID,
    title: str = Form(...),
    description: str = Form(None),
    due_date: int = Form(None),
    target_date: int = Form(None),
    users: str = Form(""),
    enable_workflow: bool = Form(False),
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

    db_subtask = models.ServiceSubtask(
        title=title,
        description=description,
        due_date=due_date,
        target_date=target_date,
        users=[str(uuid.UUID(user_id)) for user_id in users.split(",")] if users else [],
        enable_workflow=enable_workflow,
        service_id=service_id,
    )
    db.add(db_subtask)
    db.commit()
    db.refresh(db_subtask)
    return db_subtask

@router.get("/subtasks/{service_id}", response_model=List[schemas.Subtask], dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def get_subtasks(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    subtasks = db.query(models.ServiceSubtask).filter(models.ServiceSubtask.service_id == service_id).all()
    return subtasks

@router.delete("/subtasks/{subtask_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def delete_subtask(
    subtask_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_subtask = db.query(models.ServiceSubtask).filter(models.ServiceSubtask.id == subtask_id).first()
    if db_subtask is None:
        raise HTTPException(status_code=404, detail="Subtask not found")
    db.delete(db_subtask)
    db.commit()


@router.patch("/subtasks/{subtask_id}", response_model=schemas.Subtask, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def update_subtask(
    subtask_id: uuid.UUID,
    subtask_in: schemas.SubtaskUpdate,
    db: Session = Depends(get_db),
):
    db_subtask = db.query(models.ServiceSubtask).filter(models.ServiceSubtask.id == subtask_id).first()
    if db_subtask is None:
        raise HTTPException(status_code=404, detail="Subtask not found")

    update_data = subtask_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_subtask, key, value)

    db.commit()
    db.refresh(db_subtask)
    return db_subtask

@router.post("/supporting-files/{service_id}", response_model=schemas.FileRead, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT", "CA_TEAM"]))])
def upload_file(
    service_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    current_agency: dict = Depends(get_current_agency),
):
    agency_id = current_agency["id"]
    user_id = current_user["id"]
    
    db_service = (
        db.query(models.Service)
        .filter(models.Service.id == service_id, models.Service.agency_id == agency_id)
        .first()
    )
    if db_service is None:
        raise HTTPException(status_code=404, detail="Service not found")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    )
    bucket_name = config.S3_BUCKET_NAME
    file_key = f"{service_id}/{uuid.uuid4()}_{file.filename}"

    s3.upload_fileobj(file.file, bucket_name, file_key)

    db_file = models.ServiceSupportingFile(
        service_id=service_id,
        file_name=file.filename,
        file_path=f"s3://{bucket_name}/{file_key}",
        mime_type=file.content_type,
        uploaded_by=user_id,
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/supporting-files/{service_id}", response_model=List[schemas.FileRead], dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT", "CA_TEAM"]))])
def get_supporting_files(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    supporting_files = db.query(models.ServiceSupportingFile).filter(models.ServiceSupportingFile.service_id == service_id).all()
    return supporting_files

@router.delete("/supporting-files/{file_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_role(["SUPER_ADMIN", "AGENCY_ADMIN", "CA_ACCOUNTANT"]))])
def delete_supporting_file(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    db_file = db.query(models.ServiceSupportingFile).filter(models.ServiceSupportingFile.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    s3 = boto3.client(
        "s3",
        aws_access_key_id=config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY,
    )
    bucket_name = config.S3_BUCKET_NAME
    file_key = "/".join(db_file.file_path.split("/")[3:])

    s3.delete_object(Bucket=bucket_name, Key=file_key)

    db.delete(db_file)
    db.commit()
