import re
from typing import Tuple, List, Optional, Dict, Any
from src.models.schemas import ParsedFoodData, ScoreBreakdown, IngredientDetail, PersonalizedAdjustment, NutritionScorecard
from src.services import normalization_engine

def normalize_ingredient_name(raw_name: str) -> str:
    """
    Cleans percentages, punctuation, and maps spelling typos/variants.
    """
    res = normalization_engine.normalize_ingredient(raw_name)
    return res.get("name", raw_name)

def analyze_ingredient(name: str) -> IngredientDetail:
    """
    Fuzzy match ingredient label raw text against normalized centralized engine.
    """
    res = normalization_engine.normalize_ingredient(name)
    return IngredientDetail(
        name=res.get("name", name),
        category=res.get("category", "Ingredient"),
        processing_level=res.get("processing_level", 2),
        vegan=res.get("vegan", True),
        vegetarian=res.get("vegetarian", True),
        gluten_free=res.get("gluten_free", True),
        safety_notes=res.get("safety_notes", None),
        child_suitability=res.get("child_suitability", True),
        diabetic_suitability=res.get("diabetic_suitability", True),
        is_additive=res.get("is_additive", res.get("additive_type", "None") != "None"),
        is_preservative=res.get("is_preservative", "preservative" in res.get("category", "").lower()),
        is_controversial=res.get("is_controversial", False)
    )

def calculate_score(parsed_data: ParsedFoodData, health_mode: str = "General") -> Tuple[NutritionScorecard, List[ScoreBreakdown], Optional[PersonalizedAdjustment], List[IngredientDetail], Dict[str, Any]]:
    """
    Production-focused deterministic scoring engine.
    Calculates score out of 100 based on standard additives, sugars, trans fats, protein, and fiber.
    """
    ingredient_details = []
    breakdown = []
    positives = []
    negatives = []
    
    ingredients = parsed_data.ingredients
    ingredients_str = " ".join(ingredients).lower()
    
    # 1. Standardize and look up ingredients
    for ing in ingredients:
        detail = analyze_ingredient(ing)
        ingredient_details.append(detail)
        
    # 2. Compute Multi-Dimensional Parameters
    
    # NOVA processing index
    nova_group = 1
    if ingredient_details:
        nova_group = max(det.processing_level for det in ingredient_details)
        
    # Additive Density
    additive_count = sum(1 for det in ingredient_details if det.is_additive)
    if additive_count >= 4:
        additive_density = "High"
    elif additive_count >= 2:
        additive_density = "Medium"
    else:
        additive_density = "Low"
        
    # Sugar Load
    nutrition_str = str(parsed_data.nutrition).lower()
    sugar_match = re.search(r"sugar.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    
    sugar_load = "Low"
    sugar_val = 0.0
    if sugar_match:
        sugar_val = float(sugar_match.group(1))
        if sugar_val >= 15:
            sugar_load = "High"
        elif sugar_val >= 5:
            sugar_load = "Moderate"
    else:
        # Fallback based on sweetener count
        sweetener_count = sum(1 for det in ingredient_details if det.category == "Sweetener")
        if sweetener_count > 1:
            sugar_load = "High"
        elif sweetener_count == 1:
            sugar_load = "Moderate"
            
    # Sodium Load
    sodium_match = re.search(r"sodium.*?(\d+)(?:\.\d+)?\s*m?g", nutrition_str)
    sodium_load = "Low"
    if sodium_match:
        sodium_val = float(sodium_match.group(1))
        if sodium_val >= 400:
            sodium_load = "High"
        elif sodium_val >= 100:
            sodium_load = "Moderate"
    else:
        # Fallback on salt presence
        salt_count = sum(1 for det in ingredient_details if "salt" in det.name or "sodium" in det.name)
        if salt_count > 1:
            sodium_load = "High"
        elif salt_count == 1:
            sodium_load = "Moderate"
            
    # Ingredient Transparency
    if len(ingredients) <= 6:
        transparency_index = "High"
    elif len(ingredients) <= 15:
        transparency_index = "Moderate"
    else:
        transparency_index = "Low"
        
    # Protein Quality
    protein_match = re.search(r"protein.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    has_protein_source = any(d.name in ["whey protein isolate", "milk solids", "peanuts", "almonds", "nuts"] for d in ingredient_details)
    protein_quality = "Standard"
    if (protein_match and float(protein_match.group(1)) >= 5) or has_protein_source:
        protein_quality = "High Source"
        
    # Fiber Quality
    fiber_match = re.search(r"fiber.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    has_fiber_source = any(d.name in ["whole wheat", "oats", "millet", "ragi", "quinoa", "brown rice", "whole wheat flour"] for d in ingredient_details)
    fiber_quality = "Standard"
    if (fiber_match and float(fiber_match.group(1)) >= 3) or has_fiber_source:
        fiber_quality = "High Source"
        
    scorecard = NutritionScorecard(
        nova_group=nova_group,
        additive_density=additive_density,
        sugar_load=sugar_load,
        sodium_load=sodium_load,
        transparency_index=transparency_index,
        protein_quality=protein_quality,
        fiber_quality=fiber_quality
    )

    # 3. Deterministic scoring out of 100
    score = 100

    # Added Sugar Deduction (-15)
    if sugar_load == "High":
        score -= 15
        negatives.append("Contains added sugar (-15)")
        breakdown.append(ScoreBreakdown(reason="Sugar load exceeds 15g per serving; daily guidelines suggest limiting added simple sweeteners", impact=-15))
    elif sugar_load == "Moderate":
        score -= 5
        negatives.append("Contains moderate added sugar (-5)")
        breakdown.append(ScoreBreakdown(reason="Moderate sugar load; portion monitoring is recommended", impact=-5))

    # Trans Fat Deduction (-30)
    has_trans_fat = any(
        "hydrogenated" in name.lower() or "trans fat" in name.lower() or "palmolein" in name.lower()
        for name in ingredients
    )
    if has_trans_fat:
        score -= 30
        negatives.append("Contains industrial trans fats / hydrogenated fats (-30)")
        breakdown.append(ScoreBreakdown(reason="Contains hydrogenated or trans fat ingredients linked to cardiovascular risks", impact=-30))

    # High Protein Boost (+10)
    if protein_quality == "High Source":
        score += 10
        positives.append("High in protein (+10)")
        breakdown.append(ScoreBreakdown(reason="Includes a high-quality source of dietary protein", impact=10))

    # High Fiber Boost (+10)
    if fiber_quality == "High Source":
        score += 10
        positives.append("High in fiber (+10)")
        breakdown.append(ScoreBreakdown(reason="Includes complex whole grains contributing to fiber intake", impact=10))

    # Boundary check (0-100)
    score = max(0, min(100, score))

    # Letter Grade Mapping
    if score >= 90:
        grade = "S"
    elif score >= 80:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 60:
        grade = "C"
    elif score >= 40:
        grade = "D"
    else:
        grade = "F"

    explanation_data = {
        "score": score,
        "grade": grade,
        "positives": positives if positives else ["Balanced profile"],
        "negatives": negatives if negatives else ["No major concerns"]
    }

    # 4. Personalization Adjustments
    adjustment = None
    
    if health_mode == "Diabetic Friendly":
        diabetic_reasons = []
        if sugar_load == "High" or any(det.category == "Sweetener" for det in ingredient_details):
            diabetic_reasons.append("sweetener index is elevated")
        if any(d.name in ["maida", "refined wheat flour"] for d in ingredient_details):
            diabetic_reasons.append("contains refined maida flours causing glycemic spikes")
            
        if diabetic_reasons:
            adjustment = PersonalizedAdjustment(
                active_mode="Diabetic Friendly",
                reason=f"Diabetic Caution: {'; '.join(diabetic_reasons)}. Portions should be carefully regulated."
            )
            
    elif health_mode == "Child Friendly":
        child_reasons = []
        c_colors = [d.name for d in ingredient_details if d.category == "Color"]
        if c_colors:
            child_reasons.append(f"contains synthetic dyes ({', '.join(c_colors)})")
        if any(d.is_preservative for d in ingredient_details):
            child_reasons.append("includes chemical preservatives")
            
        if child_reasons:
            adjustment = PersonalizedAdjustment(
                active_mode="Child Friendly",
                reason=f"Child profile caution: {', '.join(child_reasons)}. Moderation is standardly recommended for children."
            )
            
    elif health_mode == "Vegetarian":
        non_veg = [det.name for det in ingredient_details if not det.vegetarian]
        if non_veg:
            score = max(0, score - 20)  # Apply deduction for diet mismatch
            adjustment = PersonalizedAdjustment(
                active_mode="Vegetarian",
                reason=f"Failed vegetarian criteria: Contains animal-derived ingredients ({', '.join(non_veg)})"
            )
            
    elif health_mode == "Vegan":
        non_vegan = [det.name for det in ingredient_details if not det.vegan]
        if non_vegan:
            score = max(0, score - 20)
            adjustment = PersonalizedAdjustment(
                active_mode="Vegan",
                reason=f"Failed vegan criteria: Contains dairy or animal-derived ingredients ({', '.join(non_vegan)})"
            )

    return scorecard, breakdown, adjustment, ingredient_details, explanation_data
