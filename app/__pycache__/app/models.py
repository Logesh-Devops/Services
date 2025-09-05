import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Integer,
    Enum,
    Date,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Service(Base):
    __tablename__ = "services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agency_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String, nullable=False)
    is_enabled = Column(Boolean, default=True)
    is_checklist_completion_required = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)
    auto_task_creation_frequency = Column(
        Enum("monthly", "quarterly", "half_yearly", "yearly", name="auto_task_creation_frequency"),
        nullable=True,
    )
    target_date_creation_date = Column(Integer, nullable=True)
    assign_auto_tasks_to_users_of_respective_clients = Column(Boolean, default=False)
    assign_auto_tasks_to_users = Column(JSON, nullable=True)
    billing_sac_code = Column(String, nullable=True)
    billing_gst_percent = Column(Numeric(5, 2), default=0.00)
    billing_default_rate = Column(Numeric(12, 2), default=0.00)
    billing_default_billable = Column(Boolean, default=True)
    create_document_collection_request_automatically = Column(Boolean, default=False)
    document_request_default_message = Column(String, nullable=True)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    checklists = relationship("ServiceChecklist", back_populates="service", cascade="all, delete-orphan")
    subtasks = relationship("ServiceSubtask", back_populates="service", cascade="all, delete-orphan")
    supporting_files = relationship("ServiceSupportingFile", back_populates="service", cascade="all, delete-orphan")
    clients = relationship("ClientService", back_populates="service", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("agency_id", "name", name="uq_agency_id_name"),)


class ServiceChecklist(Base):
    __tablename__ = "service_checklists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    item_text = Column(String, nullable=False)
    is_required = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    service = relationship("Service", back_populates="checklists")


class ServiceSubtask(Base):
    __tablename__ = "service_subtasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(Integer, nullable=True)
    target_date = Column(Integer, nullable=True)
    users = Column(JSON, nullable=True)
    enable_workflow = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)

    service = relationship("Service", back_populates="subtasks")


class ClientService(Base):
    __tablename__ = "client_services"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=False)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)

    service = relationship("Service", back_populates="clients")


class ServiceSupportingFile(Base):
    __tablename__ = "service_supporting_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    uploaded_by = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    service = relationship("Service", back_populates="supporting_files")
