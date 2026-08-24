from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .database import Base
import uuid

class ComplaintCategory(str, Enum):
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    STRUCTURAL = "structural"
    CLEANLINESS = "cleanliness"
    NOISE = "noise"
    PARKING = "parking"
    COMMON_AREA = "common_area"
    OTHER = "other"

class ComplaintStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class ComplaintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Complaint(Base):
    __tablename__ = "complaints"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(SQLEnum(ComplaintCategory), nullable=False)
    description = Column(Text, nullable=False)
    photo_url = Column(String, nullable=True)
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.OPEN, index=True)
    priority = Column(SQLEnum(ComplaintPriority), default=ComplaintPriority.MEDIUM)
    is_overdue = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    days_to_overdue = Column(Integer, default=7)
    
    resident = relationship("User", back_populates="complaints")
    history = relationship("ComplaintHistory", back_populates="complaint", cascade="all, delete-orphan")

class ComplaintHistory(Base):
    __tablename__ = "complaint_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = Column(String, ForeignKey("complaints.id"), nullable=False, index=True)
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(ComplaintStatus), nullable=False)
    priority = Column(SQLEnum(ComplaintPriority), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    complaint = relationship("Complaint", back_populates="history")
    created_by = relationship("User", back_populates="complaint_history")
