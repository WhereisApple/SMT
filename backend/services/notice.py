from sqlalchemy.orm import Session
from models.notice import Notice
from utils.email import send_important_notice_email
from models.user import User, UserRole

class NoticeService:
    @staticmethod
    def create_notice(db: Session, admin_id: str, title: str, content: str, is_important: bool = False):
        """Create a new notice"""
        notice = Notice(
            admin_id=admin_id,
            title=title,
            content=content,
            is_important=is_important
        )
        db.add(notice)
        db.commit()
        db.refresh(notice)
        return notice
    
    @staticmethod
    def get_all_notices(db: Session):
        """Get all notices, important ones first"""
        return db.query(Notice).order_by(Notice.is_important.desc(), Notice.created_at.desc()).all()
    
    @staticmethod
    def get_notice_by_id(db: Session, notice_id: str):
        """Get notice by ID"""
        return db.query(Notice).filter(Notice.id == notice_id).first()
    
    @staticmethod
    async def update_notice(db: Session, notice_id: str, title: str = None, content: str = None, is_important: bool = None):
        """Update a notice"""
        notice = NoticeService.get_notice_by_id(db, notice_id)
        if not notice:
            return None
        
        if title:
            notice.title = title
        if content:
            notice.content = content
        if is_important is not None:
            notice.is_important = is_important
        
        db.commit()
        db.refresh(notice)
        
        if is_important:
            residents = db.query(User).filter(User.role == UserRole.RESIDENT).all()
            for resident in residents:
                await send_important_notice_email(resident.email, notice.title)
        
        return notice
    
    @staticmethod
    def delete_notice(db: Session, notice_id: str):
        """Delete a notice"""
        notice = NoticeService.get_notice_by_id(db, notice_id)
        if notice:
            db.delete(notice)
            db.commit()
            return True
        return False
