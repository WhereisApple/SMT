from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db
from models.user import UserRole
from services.complaint import UserService
from services.notice import NoticeService
from utils.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/notices", tags=["notices"])

class NoticeCreate(BaseModel):
    title: str
    content: str
    is_important: bool = False

class NoticeUpdate(BaseModel):
    title: str = None
    content: str = None
    is_important: bool = None

class NoticeResponse(BaseModel):
    id: str
    title: str
    content: str
    is_important: bool
    admin_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=NoticeResponse, tags=["admin"])
async def create_notice(
    notice: NoticeCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new notice (admin only)"""
    user = UserService.get_user_by_id(db, user_id)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create notices")
    
    new_notice = NoticeService.create_notice(
        db,
        admin_id=user_id,
        title=notice.title,
        content=notice.content,
        is_important=notice.is_important
    )
    
    return new_notice

@router.get("/")
def get_all_notices(db: Session = Depends(get_db)):
    """Get all notices"""
    notices = NoticeService.get_all_notices(db)
    return notices

@router.get("/{notice_id}")
def get_notice(notice_id: str, db: Session = Depends(get_db)):
    """Get notice by ID"""
    notice = NoticeService.get_notice_by_id(db, notice_id)
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    return notice

@router.put("/{notice_id}", response_model=NoticeResponse, tags=["admin"])
async def update_notice(
    notice_id: str,
    update: NoticeUpdate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a notice (admin only)"""
    user = UserService.get_user_by_id(db, user_id)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can update notices")
    
    notice = await NoticeService.update_notice(
        db,
        notice_id,
        update.title,
        update.content,
        update.is_important
    )
    
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return notice

@router.delete("/{notice_id}", tags=["admin"])
def delete_notice(
    notice_id: str,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notice (admin only)"""
    user = UserService.get_user_by_id(db, user_id)
    if not user or user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete notices")
    
    if not NoticeService.delete_notice(db, notice_id):
        raise HTTPException(status_code=404, detail="Notice not found")
    
    return {"message": "Notice deleted successfully"}
