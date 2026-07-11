from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config.database import get_db
from src.db import crud
from src.middleware.auth_middleware import get_current_user
from src.models.schemas import UserPreferencesRequest, UserPreferencesResponse

router = APIRouter()

@router.get("/user/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user profile/health goal preferences for the authenticated user.
    """
    try:
        user = crud.get_user_preferences(db, user_id=current_user["id"])
        return UserPreferencesResponse(id=user.id, health_mode=user.health_mode)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user preferences: {str(e)}"
        )

@router.put("/user/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    request: UserPreferencesRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user health preference goal for the authenticated user.
    """
    try:
        user = crud.update_user_preferences(db, health_mode=request.health_mode, user_id=current_user["id"])
        return UserPreferencesResponse(id=user.id, health_mode=user.health_mode)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )
