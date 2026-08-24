from datetime import datetime, timedelta
from config import settings

def check_complaint_overdue(created_at: datetime, days_threshold: int = None) -> bool:
    """Check if a complaint is overdue"""
    if days_threshold is None:
        days_threshold = settings.OVERDUE_DAYS
    
    overdue_date = created_at + timedelta(days=days_threshold)
    return datetime.utcnow() > overdue_date

def get_overdue_complaints(complaints: list) -> list:
    """Filter and return overdue complaints"""
    overdue = []
    for complaint in complaints:
        if complaint.status != "resolved" and complaint.status != "closed":
            if check_complaint_overdue(complaint.created_at, complaint.days_to_overdue):
                overdue.append(complaint)
    return overdue

def calculate_days_pending(created_at: datetime) -> int:
    """Calculate days since complaint was created"""
    delta = datetime.utcnow() - created_at
    return delta.days
