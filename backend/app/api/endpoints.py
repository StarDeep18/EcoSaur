from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from app.models.schemas import (
    ExtractedTextResponse, AnalysisRequest, AnalysisResponse, 
    ChatRequest, ChatResponse, UserPreferencesRequest, UserPreferencesResponse
)
from app.services import ocr_service, scoring, ai_service, parser
from app.db import tinydb_client

router = APIRouter()

@router.post("/scan/extract", response_model=ExtractedTextResponse)
async def extract_text(file: UploadFile = File(...)):
    """
    Step 1: Accept an image, use Gemini Vision to extract ingredients and nutrition info.
    Returns the raw string for the user to review and correct.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be an image.")
        
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024: # 10MB limit
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit.")
        
    extracted_text = await ocr_service.extract_ingredients_and_nutrition(contents)
    
    # Edge Case: OCR returned empty
    if not extracted_text or len(extracted_text.strip()) < 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not detect any text in the image. Please upload a clearer picture.")
        
    return ExtractedTextResponse(raw_text=extracted_text)

@router.post("/scan/analyze", response_model=AnalysisResponse)
async def analyze_food(request: AnalysisRequest):
    """
    Step 2: Accept corrected text, parse it, run deterministic scoring, 
    and get AI explanations/alternatives.
    """
    # 1. Parse text deterministically
    parsed_data = parser.parse_text(request.corrected_text)
    
    # 2. Rule-based scoring
    score, grade, breakdown = scoring.calculate_score(parsed_data)
    
    # 3. AI Explanation & Alternative (Only if required/async)
    explanation = await ai_service.explain_score(parsed_data, score, grade, breakdown)
    alternative = await ai_service.suggest_alternative(parsed_data)
    
    # 4. Save to local TinyDB NoSQL database
    try:
        alternative_dict = {"name": alternative.name, "recipe": alternative.recipe}
        breakdown_list = [{"reason": item.reason, "impact": item.impact} for item in breakdown]
        tinydb_client.save_scan(
            corrected_text=request.corrected_text,
            score=score,
            grade=grade,
            explanation=explanation,
            alternative=alternative_dict,
            breakdown=breakdown_list
        )
    except Exception as e:
        print(f"Warning: Failed to save scan to local database: {e}")
    
    return AnalysisResponse(
        score=score,
        grade=grade,
        explanation=explanation,
        alternative=alternative,
        breakdown=breakdown
    )

@router.post("/scan/chat", response_model=ChatResponse)
async def chat_about_food(request: ChatRequest):
    """
    Step 3: Conversational UX allowing users to ask questions about the ingredients.
    """
    reply = await ai_service.chat_with_user(request.ingredients, request.history, request.message)
    return ChatResponse(reply=reply)

@router.get("/scan/barcode/{barcode}")
async def scan_barcode(barcode: str):
    """
    Phase 7: Barcode scanner integration using OpenFoodFacts.
    Returns the raw ingredients text to be dropped into the CORRECTION flow.
    """
    from app.services import barcode_service
    ingredients_text = await barcode_service.fetch_ingredients_by_barcode(barcode)
    return {"raw_text": ingredients_text}

@router.get("/scan/history")
async def get_history(limit: int = 50):
    """
    Get persistent scan history from local NoSQL database.
    """
    try:
        history = tinydb_client.get_scan_history(limit=limit)
        return history
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scan history: {str(e)}"
        )

@router.get("/user/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences():
    """
    Get user profile/health goal preferences.
    """
    try:
        prefs = tinydb_client.get_user_preferences()
        return UserPreferencesResponse(id=prefs["id"], health_mode=prefs["health_mode"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user preferences: {str(e)}"
        )

@router.put("/user/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(request: UserPreferencesRequest):
    """
    Update user health preference goal.
    """
    try:
        updated = tinydb_client.update_user_preferences(health_mode=request.health_mode)
        return UserPreferencesResponse(id=updated["id"], health_mode=updated["health_mode"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )

