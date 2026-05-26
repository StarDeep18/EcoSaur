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
    
    # 2. Upgraded Rule-based scoring with personalization
    score, grade, breakdown, adjustment, ingredient_details = scoring.calculate_score(parsed_data, health_mode=health_mode)
    
    # 3. AI Explanation & Alternative (Only if required/async)
    explanation = await ai_service.explain_score(parsed_data, score, grade, breakdown, health_mode=health_mode)
    alternative = await ai_service.suggest_alternative(parsed_data)
    
    # 4. Save to local TinyDB NoSQL database
    try:
        alternative_dict = {
            "name": alternative.name, 
            "recipe": alternative.recipe,
            "prep_time_mins": alternative.prep_time_mins or 15,
            "approx_cost_inr": alternative.approx_cost_inr or 50
        }
        breakdown_list = [{"reason": item.reason, "impact": item.impact} for item in breakdown]
        tinydb_client.save_scan(
            corrected_text=request.corrected_text,
            score=score,
            grade=grade,
            explanation=explanation,
            alternative=alternative_dict,
            breakdown=breakdown_list,
            user_id=user_id
        )
    except Exception as e:
        print(f"Warning: Failed to save scan to local database: {e}")
    
    return AnalysisResponse(
        score=score,
        grade=grade,
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
        score, grade, breakdown, adjustment, details = scoring.calculate_score(parsed, health_mode=health_mode)
        
        # Calculate visual parameters for comparison
        nova_4_count = sum(1 for d in details if d.processing_level == 4)
        processing_desc = "Ultra-Processed (NOVA 4)" if nova_4_count > 1 else ("Processed (NOVA 3)" if len(parsed.ingredients) > 10 else "Minimally Processed")
        
        additive_count = sum(1 for d in details if d.is_additive)
        additive_desc = "High" if additive_count > 3 else ("Medium" if additive_count > 1 else "Low")
        
        sugar_count = sum(1 for d in details if d.category == "Sweetener")
        sugar_desc = "High Sugar" if sugar_count > 1 else ("Moderate" if sugar_count == 1 else "Low Sugar")
        
        protein_desc = "High Quality" if any("protein" in b.reason.lower() for b in breakdown) else "Standard"
        transparency_desc = "High" if len(parsed.ingredients) <= 10 else "Low (Long chemical list)"
        
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
            score=score,
            grade=grade,
            processing_level=processing_desc,
            additive_density=additive_desc,
            sugar_level=sugar_desc,
            protein_quality=protein_desc,
            transparency_index=transparency_desc,
            key_negatives=negatives if negatives else ["No major negative ingredients detected"],
            key_positives=positives if positives else ["Standard food profile"],
            healthy_alternative=alternative_name
        ))
        
    # Generate side-by-side verdict
    card_a, card_b = cards[0], cards[1]
    if card_a.score > card_b.score:
        verdict = f"Recommendation: Choose '{card_a.product_name}' (Grade {card_a.grade}, Score {card_a.score}/100) over '{card_b.product_name}' (Grade {card_b.grade}, Score {card_b.score}/100). '{card_b.product_name}' contains more processed ingredients: {', '.join(card_b.key_negatives[:2])}. Swapping to '{card_a.product_name}' improves nutrition and reduces toxic additive intake."
    elif card_b.score > card_a.score:
        verdict = f"Recommendation: Choose '{card_b.product_name}' (Grade {card_b.grade}, Score {card_b.score}/100) over '{card_a.product_name}' (Grade {card_a.grade}, Score {card_a.score}/100). '{card_a.product_name}' has higher negative factors: {', '.join(card_a.key_negatives[:2])}. Swapping to '{card_b.product_name}' is a healthier everyday choice."
    else:
        verdict = f"Both '{card_a.product_name}' and '{card_b.product_name}' score equally ({card_a.score}/100, Grade {card_a.grade}). Choose based on personal calorie/taste preferences, or opt for a direct homemade alternative like {card_a.healthy_alternative}."
        
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

