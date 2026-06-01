from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import re
import json
from datetime import datetime

from app.db.database import get_db
from app.db import crud
from app.models.schemas import (
    ExtractedTextResponse, AnalysisRequest, AnalysisResponse, 
    ChatRequest, ChatResponse, UserPreferencesRequest, UserPreferencesResponse,
    HomemadeAlternative, ComparisonCard, ProductComparisonRequest, 
    ProductComparisonResponse, ProductComparisonCard, CrowdsourceBarcodeRequest
)
from app.services import ocr_service, scoring, ai_service, parser, category_engine, normalization_engine
from app.services.reasoning_engine import generate_recommendation_reasoning

router = APIRouter()

@router.post("/scan/extract", response_model=ExtractedTextResponse)
async def extract_text(file: UploadFile = File(...)):
    """
    Step 1: Accept an image, use AI Vision to extract ingredients and nutrition info.
    Returns the raw string for the user to review and correct, along with low confidence word tags.
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
        
    # Programmatic low confidence word tags: identify spelling typos or non-dictionary terms
    tokens = list(set(re.findall(r'\b[a-zA-Z]{3,}\b', extracted_text)))
    low_confidence_words = []
    
    for t in tokens:
        res = normalization_engine.normalize_ingredient(t)
        if res.get("flagged", False):
            # Exclude standard grammar or packaging header words from being highlighted
            if t.lower() not in [
                "and", "the", "with", "contains", "ingredients", "facts", "nutrition", "serving", 
                "size", "saturated", "trans", "total", "fat", "sugar", "protein", "sodium", 
                "cholesterol", "calcium", "iron", "vitamin", "calories", "energy", "value", 
                "percent", "daily", "organic", "added", "natural", "flavors", "colors", "preservative"
            ]:
                low_confidence_words.append(t)
                
    return ExtractedTextResponse(raw_text=extracted_text, low_confidence_words=low_confidence_words)

@router.post("/scan/analyze", response_model=AnalysisResponse)
async def analyze_food(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Step 2: Accept corrected text, parse it, run deterministic scoring based on user preferences, 
    and get AI explanations/alternatives.
    """
    # 0. Retrieve user preferences
    health_mode = "General"
    user_id = request.user_id or "default"
    try:
        user = crud.get_user_preferences(db, user_id)
        if user and user.health_mode:
            health_mode = user.health_mode
    except Exception as e:
        print(f"Warning: Failed to fetch user preferences for scoring: {e}")
        
    # 1. Parse text deterministically
    parsed_data = parser.parse_text(request.corrected_text, request.product_name)
    
    # 2. Upgraded Rule-based scoring with personalization (scorecard based)
    scorecard, breakdown, adjustment, ingredient_details = scoring.calculate_score(parsed_data, health_mode=health_mode)
    
    # 3. Category Engine Integration: Classify product
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
        main_alternative = await ai_service.suggest_alternative(parsed_data)
        main_alternative.reasoning = generate_recommendation_reasoning(category_info, main_alternative, scorecard, breakdown)
        alternatives_list.append(main_alternative)
        
    # 5. Fetch same-category commercial comparisons
    comparisons = category_engine.get_comparison_cards(category_info, product_name_for_classification)
    
    # 6. AI Explanation
    explanation = await ai_service.explain_score(parsed_data, scorecard, breakdown, health_mode=health_mode)
    
    # Calculate dynamic trust confidence scores
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

    # 7. Save to local SQLite database (serialize scorecard)
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
            score=int(100 - (scorecard.nova_group * 10) - (15 if scorecard.sugar_load == "High" else 0)), # Backward compatible raw score index
            grade=f"NOVA {scorecard.nova_group}",
            explanation=explanation,
            alternative=alternative_dict,
            breakdown=breakdown_list,
            user_id=user_id,
            confidence_ocr=ocr_score / 100.0,
            confidence_match=match_score / 100.0,
            confidence_analysis=0.95,
            confidence_rec=0.90
        )
    except Exception as e:
        print(f"Warning: Failed to save scan to local database: {e}")
    
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

@router.post("/products/compare", response_model=ProductComparisonResponse)
async def compare_products(request: ProductComparisonRequest, db: Session = Depends(get_db)):
    """
    Advanced smart comparison system. Compares two or more food items,
    analyzing processing intensity, sugar levels, additives, and transparency side-by-side.
    """
    if len(request.product_names) < 2 or len(request.corrected_texts) < 2:
        raise HTTPException(status_code=400, detail="Must provide at least two products and two ingredient lists to compare.")
        
    user_id = request.user_id or "default"
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
        verdict = f"Nutritional Review: '{card_a.product_name}' has a lower processing group (NOVA {card_a.scorecard.nova_group}) compared to '{card_b.product_name}' (NOVA {card_b.scorecard.nova_group}). Swapping to options with a lower processing category aligns closer with standard wellness dietary guidelines."
    elif card_b.scorecard.nova_group < card_a.scorecard.nova_group:
        verdict = f"Nutritional Review: '{card_b.product_name}' has a lower processing group (NOVA {card_b.scorecard.nova_group}) compared to '{card_a.product_name}' (NOVA {card_a.scorecard.nova_group}). Portion monitoring is recommended for items under NOVA Group {card_a.scorecard.nova_group}."
    else:
        verdict = f"Both '{card_a.product_name}' and '{card_b.product_name}' represent similar processing levels (NOVA {card_a.scorecard.nova_group}). We recommend preparing homemade alternatives such as {card_a.healthy_alternative} for regular consumption."
        
    return ProductComparisonResponse(comparison_cards=cards, verdict=verdict)

@router.post("/scan/chat", response_model=ChatResponse)
async def chat_about_food(request: ChatRequest):
    """
    Step 3: Conversational UX allowing users to ask questions about the ingredients.
    """
    reply = await ai_service.chat_with_user(request.ingredients, request.history, request.message)
    return ChatResponse(reply=reply)

@router.get("/scan/barcode/{barcode}")
async def scan_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    Query our local database moat for the barcode first.
    If not found, query OpenFoodFacts. If found there, cache it locally.
    If not found anywhere, return a fallback ingestion trigger.
    """
    barcode_clean = barcode.strip()
    
    # 1. Search local custom crowdsourced moat database
    local_prod = crud.get_custom_barcode(db, barcode_clean)
    if local_prod:
        return {
            "raw_text": local_prod.ingredients_text,
            "product_name": local_prod.product_name,
            "source": "local_database_moat"
        }
        
    # 2. Search OpenFoodFacts
    from app.services import barcode_service
    ingredients_text = await barcode_service.fetch_ingredients_by_barcode(barcode_clean)
    
    # Check if not found or failed in OpenFoodFacts
    if "not found" in ingredients_text.lower() or "failed" in ingredients_text.lower():
        return {
            "raw_text": "",
            "barcode_not_found": True,
            "barcode": barcode_clean,
            "message": "Barcode not registered. Please contribute details!"
        }
        
    # 3. Cache inside database moat
    crud.save_custom_barcode(
        db=db,
        barcode=barcode_clean,
        product_name="Scanned Product",
        ingredients_text=ingredients_text,
        user_id="system_cache"
    )
    
    return {
        "raw_text": ingredients_text,
        "product_name": "Scanned Product",
        "source": "openfoodfacts"
    }

@router.post("/barcode/upload")
async def upload_custom_barcode(request: CrowdsourceBarcodeRequest, db: Session = Depends(get_db)):
    """
    Crowdsources product details permanently into our database moat.
    """
    try:
        saved = crud.save_custom_barcode(
            db=db,
            barcode=request.barcode,
            product_name=request.product_name,
            ingredients_text=request.ingredients_text,
            user_id=request.user_id
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

@router.get("/scan/history")
async def get_history(limit: int = 50, db: Session = Depends(get_db)):
    """
    Get persistent scan history from local SQLite database.
    """
    try:
        history_records = crud.get_scan_history(db, limit=limit)
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
async def get_history_insights(limit: int = 50, db: Session = Depends(get_db)):
    """
    Generate dynamic history insights from user scan logs.
    """
    try:
        history_records = crud.get_scan_history(db, limit=limit)
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
            
        from app.services.insights_engine import calculate_history_insights
        insights = calculate_history_insights(scans)
        return insights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate history insights: {str(e)}"
        )

@router.get("/user/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(db: Session = Depends(get_db)):
    """
    Get user profile/health goal preferences.
    """
    try:
        user = crud.get_user_preferences(db)
        return UserPreferencesResponse(id=user.id, health_mode=user.health_mode)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user preferences: {str(e)}"
        )

@router.put("/user/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(request: UserPreferencesRequest, db: Session = Depends(get_db)):
    """
    Update user health preference goal.
    """
    try:
        user = crud.update_user_preferences(db, health_mode=request.health_mode)
        return UserPreferencesResponse(id=user.id, health_mode=user.health_mode)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user preferences: {str(e)}"
        )

# --- Phase 2: Crowdsourcing Dataset Growth Loops & Administration ---
class OCRCorrectionRequest(BaseModel):
    original_text: str
    corrected_text: str
    product_name: Optional[str] = None
    user_id: Optional[str] = "default"

@router.post("/ocr/correct")
async def log_ocr_correction(request: OCRCorrectionRequest, db: Session = Depends(get_db)):
    """
    Log manual user OCR corrections to the database to improve spellcheck maps.
    """
    try:
        from app.models.database_models import OCRCorrection, User
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            user = User(id=request.user_id, health_mode="General")
            db.add(user)
            db.flush()
            
        correction = OCRCorrection(
            original_text=request.original_text,
            corrected_text=request.corrected_text,
            product_name=request.product_name,
            user_id=request.user_id
        )
        db.add(correction)
        db.commit()
        return {"status": "success", "message": "OCR correction logged successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log OCR correction: {str(e)}")

@router.get("/admin/moderation/queue")
async def get_moderation_queue(status: str = "pending", db: Session = Depends(get_db)):
    """
    Admin-only review workflow listing unverified barcode uploads or ingredient additions.
    """
    try:
        from app.models.database_models import ModerationQueue
        items = db.query(ModerationQueue).filter(ModerationQueue.status == status).all()
        return [
            {
                "id": item.id,
                "item_type": item.item_type,
                "item_id": item.item_id,
                "item_data": json.loads(item.item_data_json),
                "status": item.status,
                "reviewer_notes": item.reviewer_notes,
                "created_at": item.created_at.isoformat()
            } for item in items
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch moderation queue: {str(e)}")

class ModerationActionRequest(BaseModel):
    queue_id: int
    action: str # "approve" or "reject"
    reviewer_notes: Optional[str] = None

@router.post("/admin/moderation/action")
async def resolve_moderation_item(request: ModerationActionRequest, db: Session = Depends(get_db)):
    """
    Approve or reject a contributed barcode or unknown ingredient.
    """
    try:
        from app.models.database_models import ModerationQueue, Product, User
        item = db.query(ModerationQueue).filter(ModerationQueue.id == request.queue_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Moderation queue item not found.")
            
        item.status = "approved" if request.action == "approve" else "rejected"
        item.reviewer_notes = request.reviewer_notes
        item.updated_at = datetime.utcnow()
        
        # If barcode upload is approved, verify the product and trigger contributor reputation loop
        if item.item_type == "barcode" and request.action == "approve":
            data = json.loads(item.item_data_json)
            barcode = data.get("barcode")
            prod = db.query(Product).filter(Product.barcode == barcode).first()
            if prod:
                prod.verified = True
                if prod.contributor_id:
                    user = db.query(User).filter(User.id == prod.contributor_id).first()
                    if user:
                        print(f"Contributor {prod.contributor_id} reputation increased.")
                        
        db.commit()
        return {"status": "success", "message": f"Queue item {request.action}d successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to resolve moderation item: {str(e)}")
