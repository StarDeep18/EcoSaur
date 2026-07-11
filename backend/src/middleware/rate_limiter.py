from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from datetime import date
from src.config.database import get_db
from src.middleware.auth_middleware import get_current_user
from src.models.database_models import APIUsage

async def check_rate_limit(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> bool:
    """
    FastAPI dependency that enforces a 10 scan/day limit.
    Checks the api_usage table in the database.
    """
    user_id = current_user["id"]
    today = date.today()
    
    usage = db.query(APIUsage).filter(
        APIUsage.user_id == user_id,
        APIUsage.date == today
    ).first()
    
    if usage and usage.scan_count >= 10:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily scan limit reached. Free tier is limited to 10 scans/day."
        )
    return True

def increment_rate_limit(user_id: str, db: Session) -> None:
    """
    Increments the user's daily scan usage count.
    """
    today = date.today()
    usage = db.query(APIUsage).filter(
        APIUsage.user_id == user_id,
        APIUsage.date == today
    ).first()
    
    if not usage:
        usage = APIUsage(user_id=user_id, date=today, scan_count=1)
        db.add(usage)
    else:
        usage.scan_count += 1
    db.commit()
