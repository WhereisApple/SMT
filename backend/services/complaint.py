from sqlalchemy.orm import Session
from models.user import User, UserRole
from models.complaint import Complaint, ComplaintStatus, ComplaintPriority, ComplaintHistory
from utils.auth import hash_password, verify_password, create_access_token
from datetime import timedelta
from config import settings
from utils.overdue import check_complaint_overdue
from utils.email import send_complaint_status_email, send_important_notice_email
from datetime import datetime

class UserService:
    @staticmethod
    def create_user(db: Session, email: str, password: str, name: str, role: UserRole, flat_number: str = None, phone: str = None):
        """Create a new user"""
        user = User(
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            flat_number=flat_number,
            phone=phone
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_email(db: Session, email: str):
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str):
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        """Authenticate user with email and password"""
        user = UserService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def create_access_token_for_user(user: User):
        """Create access token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            data={"sub": user.id, "role": user.role},
            expires_delta=access_token_expires
        )
        return token

class ComplaintService:
    @staticmethod
    def create_complaint(db: Session, resident_id: str, category: str, description: str, photo_url: str = None, priority: str = "medium"):
        """Create a new complaint"""
        complaint = Complaint(
            resident_id=resident_id,
            category=category,
            description=description,
            photo_url=photo_url,
            priority=priority
        )
        db.add(complaint)
        db.commit()
        db.refresh(complaint)
        return complaint
    
    @staticmethod
    def get_complaint_by_id(db: Session, complaint_id: str):
        """Get complaint by ID"""
        return db.query(Complaint).filter(Complaint.id == complaint_id).first()
    
    @staticmethod
    def get_complaints_by_resident(db: Session, resident_id: str):
        """Get all complaints by a resident"""
        return db.query(Complaint).filter(Complaint.resident_id == resident_id).order_by(Complaint.created_at.desc()).all()
    
    @staticmethod
    def get_all_complaints(db: Session, skip: int = 0, limit: int = 100):
        """Get all complaints with pagination"""
        return db.query(Complaint).order_by(Complaint.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def filter_complaints(db: Session, category: str = None, status: str = None, priority: str = None):
        """Filter complaints by category, status, or priority"""
        query = db.query(Complaint)
        
        if category:
            query = query.filter(Complaint.category == category)
        if status:
            query = query.filter(Complaint.status == status)
        if priority:
            query = query.filter(Complaint.priority == priority)
        
        return query.order_by(Complaint.created_at.desc()).all()
    
    @staticmethod
    async def update_complaint_status(db: Session, complaint_id: str, new_status: str, updated_by_id: str, note: str = None, priority: str = None):
        """Update complaint status and create history entry"""
        complaint = ComplaintService.get_complaint_by_id(db, complaint_id)
        if not complaint:
            return None
        
        old_status = complaint.status
        complaint.status = ComplaintStatus(new_status)
        
        if priority:
            complaint.priority = ComplaintPriority(priority)
        
        if new_status == "resolved":
            complaint.resolved_at = datetime.utcnow()
        
        # Update overdue status
        complaint.is_overdue = check_complaint_overdue(complaint.created_at, complaint.days_to_overdue) and new_status != "resolved"
        
        # Create history entry
        history = ComplaintHistory(
            complaint_id=complaint_id,
            created_by_id=updated_by_id,
            status=ComplaintStatus(new_status),
            priority=ComplaintPriority(priority) if priority else None,
            note=note
        )
        
        db.add(history)
        db.commit()
        db.refresh(complaint)
        
        # Send email to resident
        resident = complaint.resident
        await send_complaint_status_email(resident.email, complaint_id, new_status, note or "")
        
        return complaint
    
    @staticmethod
    def set_complaint_priority(db: Session, complaint_id: str, priority: str):
        """Set complaint priority"""
        complaint = ComplaintService.get_complaint_by_id(db, complaint_id)
        if complaint:
            complaint.priority = ComplaintPriority(priority)
            db.commit()
            db.refresh(complaint)
        return complaint
    
    @staticmethod
    def get_overdue_complaints(db: Session):
        """Get all overdue complaints"""
        complaints = db.query(Complaint).filter(
            Complaint.status != ComplaintStatus.RESOLVED,
            Complaint.status != ComplaintStatus.CLOSED
        ).all()
        
        overdue = []
        for complaint in complaints:
            if check_complaint_overdue(complaint.created_at, complaint.days_to_overdue):
                complaint.is_overdue = True
                overdue.append(complaint)
        
        db.commit()
        return sorted(overdue, key=lambda x: x.created_at)
    
    @staticmethod
    def get_complaint_history(db: Session, complaint_id: str):
        """Get history of a complaint"""
        return db.query(ComplaintHistory).filter(ComplaintHistory.complaint_id == complaint_id).order_by(ComplaintHistory.created_at.asc()).all()
    
    @staticmethod
    def get_dashboard_stats(db: Session):
        """Get dashboard statistics"""
        total_complaints = db.query(Complaint).count()
        open_complaints = db.query(Complaint).filter(Complaint.status == ComplaintStatus.OPEN).count()
        in_progress = db.query(Complaint).filter(Complaint.status == ComplaintStatus.IN_PROGRESS).count()
        resolved = db.query(Complaint).filter(Complaint.status == ComplaintStatus.RESOLVED).count()
        overdue = len(ComplaintService.get_overdue_complaints(db))
        
        # Count by category
        categories = {}
        for category in ["plumbing", "electrical", "structural", "cleanliness", "noise", "parking", "common_area", "other"]:
            count = db.query(Complaint).filter(Complaint.category == category).count()
            if count > 0:
                categories[category] = count
        
        return {
            "total_complaints": total_complaints,
            "open": open_complaints,
            "in_progress": in_progress,
            "resolved": resolved,
            "overdue": overdue,
            "by_category": categories
        }
