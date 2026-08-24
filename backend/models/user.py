from sqlalchemy import Column, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from .database import Base
import uuid

class UserRole(str, Enum):
    RESIDENT = "resident"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.RESIDENT)
    flat_number = Column(String, nullable=True)  # Only for residents
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(String, default="true")
    
    complaints = relationship("Complaint", back_populates="resident", cascade="all, delete-orphan")
    complaint_history = relationship("ComplaintHistory", back_populates="created_by", cascade="all, delete-orphan")
