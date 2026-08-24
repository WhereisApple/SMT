# filepath: /home/sumeet725/Desktop/Hershey/Random projects/SMT/backend/routes/complaints.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from sqlalchemy.orm import Session
from models.database import get_db
from models.complaint import Complaint, ComplaintHistory
from services.complaint import ComplaintService
from utils.auth import get_current_user
from datetime import datetime
import shutil
import os

router = APIRouter(prefix="/api/complaints", tags=["complaints"])

@router.post("/")
async def create_complaint(
    category: str = Form(...),
    description: str = Form(...),
    resident_id: int = Form(...),
    file: UploadFile = File(None),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        photo_url = None
        
        # Handle file upload
        if file:
            upload_dir = "uploads/complaints"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = f"{upload_dir}/{datetime.now().timestamp()}_{file.filename}"
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            photo_url = f"/uploads/complaints/{os.path.basename(file_path)}"
        
        # Create complaint
        complaint = Complaint(
            category=category,
            description=description,
            resident_id=resident_id,
            photo_url=photo_url,
            status="Open",
            priority="Low"
        )
        
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        
        # Add history entry
        history = ComplaintHistory(
            complaint_id=complaint.id,
            actor=current_user.name,
            action="Created",
            timestamp=datetime.now()
        )
        db.add(history)
        db.commit()
        
        return {
            "id": complaint.id,
            "category": complaint.category,
            "description": complaint.description,
            "status": complaint.status,
            "priority": complaint.priority,
            "photo_url": photo_url,
            "created_at": complaint.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
async def get_complaints(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role == "admin":
            complaints = db.query(Complaint).all()
        else:
            complaints = db.query(Complaint).filter(Complaint.resident_id == current_user.id).all()
        
        result = []
        for complaint in complaints:
            history = db.query(ComplaintHistory).filter(ComplaintHistory.complaint_id == complaint.id).all()
            result.append({
                "id": complaint.id,
                "category": complaint.category,
                "description": complaint.description,
                "status": complaint.status,
                "priority": complaint.priority,
                "photo_url": complaint.photo_url,
                "created_at": complaint.created_at,
                "history": [
                    {
                        "actor": h.actor,
                        "action": h.action,
                        "note": h.note,
                        "timestamp": h.timestamp
                    } for h in history
                ]
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{complaint_id}")
async def get_complaint(
    complaint_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        history = db.query(ComplaintHistory).filter(ComplaintHistory.complaint_id == complaint_id).all()
        
        return {
            "id": complaint.id,
            "category": complaint.category,
            "description": complaint.description,
            "status": complaint.status,
            "priority": complaint.priority,
            "photo_url": complaint.photo_url,
            "created_at": complaint.created_at,
            "history": [
                {
                    "actor": h.actor,
                    "action": h.action,
                    "note": h.note,
                    "timestamp": h.timestamp
                } for h in history
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: int,
    status: str,
    note: str = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can update status")
        
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        complaint.status = status
        db.commit()
        
        # Add history
        history = ComplaintHistory(
            complaint_id=complaint_id,
            actor=current_user.name,
            action=f"Status changed to {status}",
            note=note,
            timestamp=datetime.now()
        )
        db.add(history)
        db.commit()
        
        return {"message": "Status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{complaint_id}/priority")
async def set_complaint_priority(
    complaint_id: int,
    priority: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Only admins can set priority")
        
        complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        complaint.priority = priority
        db.commit()
        
        return {"message": "Priority updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))