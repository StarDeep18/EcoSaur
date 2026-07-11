import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.db import crud
from src.middleware.auth_middleware import get_current_user
from src.services.insights_engine import calculate_history_insights

router = APIRouter()

@router.get("/scan/history")
async def get_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get persistent scan history from database for the authenticated user.
    """
    try:
        history_records = crud.get_scan_history(db, user_id=current_user["id"], limit=limit)
        history = []
        for s in history_records:
            history.append({
                "id": s.id,
                "user_id": s.user_id,
                "date": s.date.isoformat() if s.date else "",
                "corrected_text": s.corrected_text,
                "score": s.score,
                "grade": s.grade,
                "explanation": s.explanation,
                "alternative": {
                    "name": s.alternative_name,
                    "recipe": s.alternative_recipe,
                    "prep_time_mins": s.alternative_prep_time or 15,
                    "approx_cost_inr": s.alternative_cost or 40
                },
                "breakdown": json.loads(s.breakdown_json) if s.breakdown_json else [],
                "image_url": s.image_url,
                "confidence": {
                    "ocr_score": int((s.confidence_ocr or 1.0) * 100),
                    "ocr_level": "High" if (s.confidence_ocr or 1.0) >= 0.9 else "Moderate" if (s.confidence_ocr or 1.0) >= 0.7 else "Low",
                    "match_score": int((s.confidence_match or 1.0) * 100),
                    "match_level": "High" if (s.confidence_match or 1.0) >= 0.9 else "Moderate" if (s.confidence_match or 1.0) >= 0.7 else "Low",
                }
            })
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan history: {str(e)}"
        )

@router.get("/scan/history/insights")
async def get_history_insights(
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate dynamic history insights from authenticated user's scan logs.
    """
    try:
        history_records = crud.get_scan_history(db, user_id=current_user["id"], limit=limit)
        scans = []
        for s in history_records:
            scans.append({
                "id": s.id,
                "user_id": s.user_id,
                "date": s.date.isoformat() if s.date else "",
                "corrected_text": s.corrected_text,
                "score": s.score,
                "grade": s.grade,
                "explanation": s.explanation,
                "alternative": {
                    "name": s.alternative_name,
                    "recipe": s.alternative_recipe,
                    "prep_time_mins": s.alternative_prep_time or 15,
                    "approx_cost_inr": s.alternative_cost or 40
                },
                "breakdown": json.loads(s.breakdown_json) if s.breakdown_json else []
            })
            
        insights = calculate_history_insights(scans)
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate history insights: {str(e)}"
        )

@router.delete("/scan/history")
async def delete_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes the authenticated user's scan history records.
    """
    try:
        from src.models.database_models import Scan
        db.query(Scan).filter(Scan.user_id == current_user["id"]).delete()
        db.commit()
        return {"status": "success", "message": "Scan history cleared successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear scan history: {str(e)}"
        )
