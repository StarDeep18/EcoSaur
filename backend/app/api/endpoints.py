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
    Step 2: Accept corrected text, parse it, run deterministic scoring based on user preferences, 
    and get AI explanations/alternatives.
    """
    # 0. Retrieve user preferences
    health_mode = "General"
    user_id = request.user_id or "default"
    try:
        prefs = tinydb_client.get_user_preferences(user_id)
        if prefs and "health_mode" in prefs:
            health_mode = prefs["health_mode"]
    except Exception as e:
        print(f"Warning: Failed to fetch user preferences for scoring: {e}")
        
    # 1. Parse text deterministically
    parsed_data = parser.parse_text(request.corrected_text, request.product_name)
    
    # 2. Upgraded Rule-based scoring with personalization (scorecard based)
    scorecard, breakdown, adjustment, ingredient_details = scoring.calculate_score(parsed_data, health_mode=health_mode)
    
    # 3. AI Explanation & Alternative (Only if required/async)
    explanation = await ai_service.explain_score(parsed_data, scorecard, breakdown, health_mode=health_mode)
    alternative = await ai_service.suggest_alternative(parsed_data)
    
    # 4. Save to local TinyDB NoSQL database (serialize scorecard)
    try:
        alternative_dict = {
            "name": alternative.name, 
            "recipe": alternative.recipe,
            "prep_time_mins": alternative.prep_time_mins or 15,
            "approx_cost_inr": alternative.approx_cost_inr or 40
        }
        breakdown_list = [{"reason": item.reason, "impact": item.impact} for item in breakdown]
        scorecard_dict = scorecard.model_dump()
        tinydb_client.save_scan(
            corrected_text=request.corrected_text,
            score=int(100 - (scorecard.nova_group * 10) - (15 if scorecard.sugar_load == "High" else 0)), # Backward compatible raw score index
            grade=f"NOVA {scorecard.nova_group}",
            explanation=explanation,
            alternative=alternative_dict,
            breakdown=breakdown_list,
            user_id=user_id
        )
    except Exception as e:
        print(f"Warning: Failed to save scan to local database: {e}")
    
    return AnalysisResponse(
        scorecard=scorecard,
        explanation=explanation,
        alternative=alternative,
        breakdown=breakdown,
        personalized_adjustments=adjustment,
        ingredient_details=ingredient_details
    )

from app.models.schemas import ProductComparisonRequest, ProductComparisonResponse, ProductComparisonCard

@router.post("/products/compare", response_model=ProductComparisonResponse)
async def compare_products(request: ProductComparisonRequest):
    """
    Advanced smart comparison system. Compares two or more food items,
    analyzing processing intensity, sugar levels, additives, and transparency side-by-side.
    """
    if len(request.product_names) < 2 or len(request.corrected_texts) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least two products and two ingredient lists to compare.")
        
    user_id = request.user_id or "default"
    health_mode = "General"
    try:
        prefs = tinydb_client.get_user_preferences(user_id)
        if prefs and "health_mode" in prefs:
            health_mode = prefs["health_mode"]
    except Exception as e:
        print(f"Warning: Failed to fetch user preferences: {e}")
        
    cards = []
    
    for idx, name in enumerate(request.product_names):
        corr_text = request.corrected_texts[idx]
        # Parse & score
        parsed = parser.parse_text(corr_text, name)
        scorecard, breakdown, adjustment, details = scoring.calculate_score(parsed, health_mode=health_mode)
        
        negatives = [b.reason for b in breakdown if b.impact < 0][:3]
        positives = [b.reason for b in breakdown if b.impact > 0][:3]
        
        # Simple local recipe suggestion
        alternative_name = f"Homemade healthy {name}"
        if "biscuit" in name.lower() or "cookie" in name.lower():
            alternative_name = "Baked Ragi & Oats Cookies"
        elif "chip" in name.lower() or "crisp" in name.lower():
            alternative_name = "Roasted Spiced Makhana"
        elif "noodle" in name.lower():
            alternative_name = "Vegetable Semiya Upma"
            
        cards.append(ProductComparisonCard(
            product_name=name,
            scorecard=scorecard,
            key_negatives=negatives if negatives else ["No major concerns detected"],
            key_positives=positives if positives else ["Standard snack profile"],
            healthy_alternative=alternative_name
        ))
        
    # Generate side-by-side verdict (evidence-aware and non-alarmist)
    card_a, card_b = cards[0], cards[1]
    
    if card_a.scorecard.nova_group < card_b.scorecard.nova_group:
        verdict = f"Nutritional Review: '{card_a.product_name}' has a lower processing group (NOVA {card_a.scorecard.nova_group}) compared to '{card_b.product_name}' (NOVA {card_b.scorecard.nova_group}). Moderation is commonly recommended for items containing high added sweeteners or chemical thickeners. Option '{card_a.product_name}' represents a more traditional culinary option."
    elif card_b.scorecard.nova_group < card_a.scorecard.nova_group:
        verdict = f"Nutritional Review: '{card_b.product_name}' has a lower processing group (NOVA {card_b.scorecard.nova_group}) compared to '{card_a.product_name}' (NOVA {card_a.scorecard.nova_group}). Portions should be monitored for processed items. Swapping to '{card_b.product_name}' aligns closer with standard daily energy guidelines."
    else:
        verdict = f"Both '{card_a.product_name}' and '{card_b.product_name}' represent similar processing levels (NOVA {card_a.scorecard.nova_group}). Consumers are advised to verify portion sizes and consider direct whole grain culinary swaps like {card_a.healthy_alternative}."
        
    return ProductComparisonResponse(comparison_cards=cards, verdict=verdict)

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

