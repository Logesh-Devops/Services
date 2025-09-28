from pydantic import BaseModel
import uuid
from datetime import datetime

class AuditLogBase(BaseModel):
    action: str
    details: str

class AuditLogCreate(AuditLogBase):
    pass

class AuditLog(AuditLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    timestamp: datetime

    class Config:
        orm_mode = True
