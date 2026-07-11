import re
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.config.database import get_db
from src.db import crud
from src.models.schemas import (
    ExtractedTextResponse, AnalysisRequest, AnalysisResponse, 
    ChatRequest, ChatResponse, UserPreferencesRequest, UserPreferencesResponse,
    HomemadeAlternative, ComparisonCard, ProductComparisonRequest, 
    ProductComparisonResponse, ProductComparisonCard, CrowdsourceBarcodeRequest,
    OCRCorrectionRequest, OCRCorrectionResponse, RecommendationExplainRequest,
    RecommendationExplainResponse
)
from src.services import ocr_service, scoring_service, gemini_service, barcode_service, category_engine, normalization_engine
from src.services.reasoning_engine import generate_recommendation_reasoning
from src.middleware.auth_middleware import get_current_user
from src.middleware.rate_limiter import check_rate_limit, increment_rate_limit

router = APIRouter()

@router.post("/scan/extract", response_model=ExtractedTextResponse)
async def extract_text(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Step 1: Accept an image, use AI Vision to extract ingredients and nutrition info.
    Protected by JWT.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must be an image.")
        
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024: # 10MB limit
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit.")
        
    extracted_text = await ocr_service.extract_ingredients_and_nutrition(contents)
    
    if not extracted_text or len(extracted_text.strip()) < 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not detect any text in the image. Please upload a clearer picture.")
        
    tokens = list(set(re.findall(r'\b[a-zA-Z]{3,}\b', extracted_text)))
    low_confidence_words = []
    
    for t in tokens:
        res = normalization_engine.normalize_ingredient(t)
        if res.get("flagged", False):
            if t.lower() not in [
                "and", "the", "with", "contains", "ingredients", "facts", "nutrition", "serving", 
                "size", "saturated", "trans", "total", "fat", "sugar", "protein", "sodium", 
                "cholesterol", "calcium", "iron", "vitamin", "calories", "energy", "value", 
                "percent", "daily", "organic", "added", "natural", "flavors", "colors", "preservative"
            ]:
                low_confidence_words.append(t)
                
    return ExtractedTextResponse(raw_text=extracted_text, low_confidence_words=low_confidence_words)

@router.post("/scan/analyze", response_model=AnalysisResponse, dependencies=[Depends(check_rate_limit)])
async def analyze_food(
    request: AnalysisRequest, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Step 2: Accept corrected text, parse it, run deterministic scoring based on user preferences, 
    and get AI explanations/alternatives.
    Protected by JWT and rate limited to 10 scans/day.
    """
    user_id = current_user["id"]
    health_mode = "General"
    try:
        user = crud.get_user_preferences(db, user_id)
        if user and user.health_mode:
            health_mode = user.health_mode
    except Exception as e:
        print(f"Warning: Failed to fetch user preferences: {e}")
        
    # 1. Parse text structurally via Gemini
    parsed_data = gemini_service.parse_text(request.corrected_text, request.product_name)
    
    # 2. Upgraded Deterministic scoring scorecard based
    scorecard, breakdown, adjustment, ingredient_details, explanation_data = scoring_service.calculate_score(parsed_data, health_mode=health_mode)
    
    # 3. Category Engine Integration
    product_name_for_classification = request.product_name or parsed_data.product_name or "snack"
    category_info = category_engine.classify_product(product_name_for_classification, parsed_data.ingredients)
    
    # 4. Get ranked alternatives
    ranked_alts = category_engine.rank_alternatives(category_info)
    
    alternatives_list = []
    if ranked_alts:
        for alt in ranked_alts[:3]:
            dummy_alt = HomemadeAlternative(
                name=alt["name"],
                recipe=alt["recipe"],
                prep_time_mins=alt["prep_time_mins"],
                approx_cost_inr=alt["approx_cost_inr"]
            )
            dummy_alt.reasoning = generate_recommendation_reasoning(category_info, dummy_alt, scorecard, breakdown)
            alternatives_list.append(dummy_alt)
        main_alternative = alternatives_list[0]
    else:
        # Fallback to AI Service
        main_alternative = await gemini_service.suggest_alternative(parsed_data)
        main_alternative.reasoning = generate_recommendation_reasoning(category_info, main_alternative, scorecard, breakdown)
        alternatives_list.append(main_alternative)
        
    # 5. Fetch same-category comparisons
    comparisons = category_engine.get_comparison_cards(category_info, product_name_for_classification)
    
    # 6. AI Explanation using restricted deterministic parameters
    explanation = await gemini_service.explain_score(parsed_data, scorecard, breakdown, health_mode=health_mode)
    
    # Calculate trust levels
    total_ings = len(ingredient_details)
    unrecognized_ings = sum(1 for det in ingredient_details if det.category == "Ingredient" and det.safety_notes and "Culinary ingredient" in det.safety_notes)
    
    match_score = 100
    if total_ings > 0:
        match_score = max(40, int(((total_ings - unrecognized_ings) / total_ings) * 100))
        
    ocr_score = 95
    if unrecognized_ings > 3:
        ocr_score = 72
    elif unrecognized_ings > 1:
        ocr_score = 86
        
    ocr_level = "High" if ocr_score >= 90 else "Moderate" if ocr_score >= 70 else "Low"
    match_level = "High" if match_score >= 90 else "Moderate" if match_score >= 70 else "Low"
    
    confidence_data = {
        "ocr_score": ocr_score,
        "ocr_level": ocr_level,
        "match_score": match_score,
        "match_level": match_level
    }

    # 7. Save scan record into database
    try:
        alternative_dict = {
            "name": main_alternative.name, 
            "recipe": main_alternative.recipe,
            "prep_time_mins": main_alternative.prep_time_mins or 15,
            "approx_cost_inr": main_alternative.approx_cost_inr or 40
        }
        breakdown_list = [{"reason": item.reason, "impact": item.impact} for item in breakdown]
        crud.save_scan(
            db=db,
            corrected_text=request.corrected_text,
            score=explanation_data["score"],
            grade=explanation_data["grade"],
            explanation=explanation,
            alternative=alternative_dict,
            breakdown=breakdown_list,
            user_id=user_id,
            image_url=request.image_url,
            confidence_ocr=ocr_score / 100.0,
            confidence_match=match_score / 100.0,
            confidence_analysis=0.95,
            confidence_rec=0.90
        )
    except Exception as e:
        print(f"Warning: Failed to save scan record: {e}")
    
    # 8. Increment user API limit count
    try:
        increment_rate_limit(user_id, db)
    except Exception as e:
        print(f"Warning: Failed to increment usage count: {e}")
        
    return AnalysisResponse(
        scorecard=scorecard,
        explanation=explanation,
        alternative=main_alternative,
        breakdown=breakdown,
        personalized_adjustments=adjustment,
        ingredient_details=ingredient_details,
        category_info=category_info.model_dump() if hasattr(category_info, "model_dump") else category_info,
        alternatives=[alt.model_dump() if hasattr(alt, "model_dump") else alt for alt in alternatives_list],
        comparisons=[c.model_dump() if hasattr(c, "model_dump") else c for c in comparisons],
        confidence=confidence_data
    )

@router.post("/product/compare", response_model=ProductComparisonResponse)
async def compare_products(
    request: ProductComparisonRequest, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Smart side-by-side product comparison.
    Protected by JWT.
    """
    if len(request.product_names) < 2 or len(request.corrected_texts) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least two products and two ingredient lists to compare.")
        
    user_id = current_user["id"]
    health_mode = "General"
    try:
        user = crud.get_user_preferences(db, user_id)
        if user and user.health_mode:
            health_mode = user.health_mode
    except Exception as e:
        print(f"Warning: Failed to fetch user preferences: {e}")
        
    cards = []
    
    for idx, name in enumerate(request.product_names):
        corr_text = request.corrected_texts[idx]
        parsed = gemini_service.parse_text(corr_text, name)
        scorecard, breakdown, adjustment, details, explanation_data = scoring_service.calculate_score(parsed, health_mode=health_mode)
        
        negatives = [b.reason for b in breakdown if b.impact < 0][:3]
        positives = [b.reason for b in breakdown if b.impact > 0][:3]
        
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
        
    card_a, card_b = cards[0], cards[1]
    
    if card_a.scorecard.nova_group < card_b.scorecard.nova_group:
        verdict = f"Nutritional Review: '{card_a.product_name}' has a lower processing group (NOVA {card_a.scorecard.nova_group}) compared to '{card_b.product_name}' (NOVA {card_b.scorecard.nova_group}). Swapping to options with a lower processing category aligns closer with standard wellness dietary guidelines."
    elif card_b.scorecard.nova_group < card_a.scorecard.nova_group:
        verdict = f"Nutritional Review: '{card_b.product_name}' has a lower processing group (NOVA {card_b.scorecard.nova_group}) compared to '{card_a.product_name}' (NOVA {card_a.scorecard.nova_group}). Portion monitoring is recommended for items under NOVA Group {card_a.scorecard.nova_group}."
    else:
        verdict = f"Both '{card_a.product_name}' and '{card_b.product_name}' represent similar processing levels (NOVA {card_a.scorecard.nova_group}). We recommend preparing homemade alternatives such as {card_a.healthy_alternative} for regular consumption."
        
    return ProductComparisonResponse(comparison_cards=cards, verdict=verdict)

@router.post("/scan/chat", response_model=ChatResponse)
async def chat_about_food(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Conversational QA assistant about ingredients.
    Protected by JWT.
    """
    reply = await gemini_service.chat_with_user(request.ingredients, request.history, request.message)
    return ChatResponse(reply=reply)

async def barcode_lookup_impl(barcode: str, db: Session, user_id: str):
    barcode_clean = barcode.strip()
    
    local_prod = crud.get_custom_barcode(db, barcode_clean)
    if local_prod:
        return {
            "raw_text": local_prod.ingredients_text,
            "product_name": local_prod.product_name,
            "source": "local_database_moat"
        }
        
    ingredients_text = await barcode_service.fetch_ingredients_by_barcode(barcode_clean)
    
    if "not found" in ingredients_text.lower() or "failed" in ingredients_text.lower():
        return {
            "raw_text": "",
            "barcode_not_found": True,
            "barcode": barcode_clean,
            "message": "Barcode not registered. Please contribute details!"
        }
        
    crud.save_custom_barcode(
        db=db,
        barcode=barcode_clean,
        product_name="Scanned Product",
        ingredients_text=ingredients_text,
        user_id=user_id
    )
    
    return {
        "raw_text": ingredients_text,
        "product_name": "Scanned Product",
        "source": "openfoodfacts"
    }

@router.get("/barcode/lookup/{barcode}")
async def lookup_barcode(
    barcode: str, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Checks barcode local database, open food facts, and caches locally.
    Protected by JWT.
    """
    return await barcode_lookup_impl(barcode, db, current_user["id"])

@router.post("/barcode/upload")
async def upload_custom_barcode(
    request: CrowdsourceBarcodeRequest, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crowdsource barcode submission into local product cache.
    Protected by JWT.
    """
    try:
        saved = crud.save_custom_barcode(
            db=db,
            barcode=request.barcode,
            product_name=request.product_name,
            ingredients_text=request.ingredients_text,
            user_id=current_user["id"]
        )
        return {
            "status": "success", 
            "message": "Product saved permanently to database moat.", 
            "product": {
                "barcode": saved.barcode,
                "product_name": saved.product_name,
                "ingredients_text": saved.ingredients_text,
                "verified": saved.verified
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save crowdsourced product: {str(e)}")

@router.post("/ocr/correct", response_model=OCRCorrectionResponse)
async def log_ocr_correction(
    request: OCRCorrectionRequest, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logs user manual spellcheck OCR adjustments in database.
    Protected by JWT.
    """
    try:
        from src.models.database_models import OCRCorrection, User
        user_id = current_user["id"]
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(id=user_id, email=current_user["email"], health_mode="General")
            db.add(user)
            db.flush()
            
        correction = OCRCorrection(
            original_text=request.original_text,
            corrected_text=request.corrected_text,
            product_name=request.product_name,
            user_id=user_id
        )
        db.add(correction)
        db.commit()
        return OCRCorrectionResponse(status="success", message="OCR correction logged successfully.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log OCR correction: {str(e)}")

@router.post("/recommendation/explain", response_model=RecommendationExplainResponse)
async def explain_recommendation(request: RecommendationExplainRequest):
    """
    Explains custom recipe swaps against scanned attributes.
    """
    try:
        reasoning = generate_recommendation_reasoning(
            request.category_info,
            request.alternative,
            request.scorecard,
            request.breakdown
        )
        return RecommendationExplainResponse(**reasoning)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compile recommendation reasoning: {str(e)}"
        )
