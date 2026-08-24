from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from models.database import get_db
from models.user import UserRole
from services.complaint import UserService, ComplaintService
from utils.auth import get_current_user, validate_email, validate_password
from utils.supabase import upload_complaint_photo
from pydantic import BaseModel, EmailStr
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/api/auth", tags=["authentication"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    flat_number: str = None
    phone: str = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str
    name: str

@router.post("/register/resident", response_model=TokenResponse)
def register_resident(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new resident"""
    if not validate_email(request.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if UserService.get_user_by_email(db, request.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if not validate_password(request.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with 1 uppercase and 1 digit"
        )
    
    user = UserService.create_user(
        db,
        email=request.email,
        password=request.password,
        name=request.name,
        role=UserRole.RESIDENT,
        flat_number=request.flat_number,
        phone=request.phone
    )
    
    token = UserService.create_access_token_for_user(user)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        name=user.name
    )

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login user with email and password"""
    user = UserService.authenticate_user(db, request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = UserService.create_access_token_for_user(user)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        role=user.role,
        name=user.name
    )

@router.get("/me")
def get_current_user_info(user_id: str = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get current user information"""
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "flat_number": user.flat_number,
        "phone": user.phone
    }
