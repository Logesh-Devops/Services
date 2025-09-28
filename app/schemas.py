import uuid
from datetime import date, datetime
from typing import Optional, List, Literal
from enum import Enum

from pydantic import BaseModel, Field, validator


class AutoTaskCreationFrequency(str, Enum):
    monthly = "monthly"
    quarterly = "quarterly"
    half_yearly = "half_yearly"
    annually = "annually"


# --- Service Schemas ---
class ServiceBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_enabled: bool = True
    is_checklist_completion_required: bool = False
    is_recurring: bool = False
    auto_task_creation_frequency: Optional[AutoTaskCreationFrequency] = None
    target_date_creation_date: Optional[int] = Field(None, ge=0)
    assign_auto_tasks_to_users_of_respective_clients: bool = False
    assign_auto_tasks_to_users: Optional[List[uuid.UUID]] = None
    create_document_collection_request_automatically: bool = False

    @validator("auto_task_creation_frequency", pre=True, always=True)
    def check_auto_task_creation_frequency(cls, v, values):
        if values.get("is_recurring") and v is None:
            raise ValueError("Auto task creation frequency is required for recurring services")
        if not values.get("is_recurring"):
            return None
        return v


class ServiceCreate(BaseModel):
    name: str


class ServiceRead(ServiceBase):
    id: uuid.UUID
    created_by: str
    created_at: datetime
    checklists: List["ChecklistItem"] = []

    class Config:
        from_attributes = True


# --- Checklist Schemas ---
class ChecklistItemCreate(BaseModel):
    item_text: str
    is_required: bool = False


class ChecklistItem(ChecklistItemCreate):
    id: uuid.UUID
    service_id: uuid.UUID
    sort_order: int

    class Config:
        from_attributes = True


class ChecklistItemUpdate(BaseModel):
    item_text: Optional[str] = None
    is_required: Optional[bool] = None
    sort_order: Optional[int] = None


# --- Subtask Schemas ---
class SubtaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[int] = None
    target_date: Optional[int] = None
    users: Optional[List[uuid.UUID]] = None
    enable_workflow: Optional[bool] = False


class Subtask(SubtaskCreate):
    id: uuid.UUID
    service_id: uuid.UUID
    sort_order: int

    class Config:
        from_attributes = True


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[int] = None
    target_date: Optional[int] = None
    users: Optional[List[uuid.UUID]] = None
    enable_workflow: Optional[bool] = None
    sort_order: Optional[int] = None



# --- File Schemas ---
class FileRead(BaseModel):
    id: uuid.UUID
    service_id: uuid.UUID
    file_name: str
    file_path: str
    mime_type: Optional[str]
    uploaded_by: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Client Service Schemas ---
class ClientService(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    service_id: uuid.UUID

    class Config:
        from_attributes = True
