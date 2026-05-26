from app.models.schemas import ParsedFoodData, ScoreBreakdown, IngredientDetail, PersonalizedAdjustment
from typing import Tuple, List, Optional, Dict, Any
import re

# Comprehensive Dictionary for Structured Ingredient Intelligence
INGREDIENT_DICTIONARY = {
    "sugar": {
        "category": "Sweetener",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Refined carbohydrate. Spike insulin and blood glucose levels; excessive consumption linked to weight gain.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "cane sugar": {
        "category": "Sweetener",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Refined sugar extracted from sugar cane. Triggers rapid glycemic spikes.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "corn syrup": {
        "category": "Sweetener",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Highly refined syrup containing high fructose levels. Strongly associated with fatty liver disease.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "gym_suitability": False,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "maltodextrin": {
        "category": "Sweetener/Thickener",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Highly processed starch with a glycemic index higher than table sugar. Rapidly raises blood sugar.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "dextrose": {
        "category": "Sweetener",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Simple sugar identical to blood glucose. Triggers immediate glycemic spike.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "jaggery": {
        "category": "Sweetener",
        "processing_level": 2,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Unrefined sugar containing trace minerals, but still high glycemic index. Better than refined sugar, but diabetic caution.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "honey": {
        "category": "Sweetener",
        "processing_level": 1,
        "vegan": False,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Natural sugar produced by bees. Anti-bacterial properties, but still acts as a simple sugar.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "palm oil": {
        "category": "Fat / Oil",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "High saturated fat content. Environmental controversy regarding deforestation. Linked to cardiovascular risks.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": True
    },
    "palmolein": {
        "category": "Fat / Oil",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Liquid fraction of palm oil. Very common in commercial Indian snacks due to low cost and high shelf life; rich in saturated fats.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": True
    },
    "hydrogenated vegetable oil": {
        "category": "Fat / Oil",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Primary source of industrial trans fats. Highly dangerous for cardiovascular health. Avoid entirely.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "gym_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": True
    },
    "maida": {
        "category": "Grain / Flour",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": False,
        "safety_notes": "Refined wheat flour stripped of fiber and nutrients. Triggers quick digestion, low satiety, and glycemic spikes.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "gym_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "refined wheat flour": {
        "category": "Grain / Flour",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": False,
        "safety_notes": "Standard refined maida flour. Fiber and bran are removed during industrial milling.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "gym_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "sodium benzoate": {
        "category": "Preservative",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Chemical preservative (E211). When combined with vitamin C, it can form benzene (a known carcinogen).",
        "child_suitability": False,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": True,
        "is_controversial": True
    },
    "potassium sorbate": {
        "category": "Preservative",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Widely used chemical preservative (E202) to prevent mold growth. Generally recognized as safe in low amounts.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": True,
        "is_controversial": False
    },
    "tartrazine": {
        "category": "Color",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Synthetic yellow food dye (E102). Linked to hyperactivity in children and hypersensitivity reactions.",
        "child_suitability": False,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "sunset yellow": {
        "category": "Color",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Synthetic orange food dye (E110). Linked to child hyperactivity and allergic symptoms.",
        "child_suitability": False,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "gelatin": {
        "category": "Animal Derivative",
        "processing_level": 3,
        "vegan": False,
        "vegetarian": False,
        "gluten_free": True,
        "safety_notes": "Protein obtained by boiling animal skin, tendons, ligaments, and bones. Not suitable for vegetarians/vegans.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "milk solids": {
        "category": "Dairy Product",
        "processing_level": 3,
        "vegan": False,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Concentrated milk components. Contain natural lactose. High calcium, but not suitable for vegans.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "whey protein isolate": {
        "category": "Protein Supplement",
        "processing_level": 3,
        "vegan": False,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Fast-digesting, high-quality dairy protein. Extremely suitable for gym and active fitness profiles.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "monosodium glutamate": {
        "category": "Flavour Enhancer",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "MSG (E621). Imparts an intensely savory umami taste. Controversial due to claims of causing headaches, though evidence is weak.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "salt": {
        "category": "Mineral",
        "processing_level": 2,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Essential nutrient, but high consumption is strongly linked to high blood pressure and cardiac stress.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "gym_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    }
}

# Standard ingredient detection helper
def analyze_ingredient(name: str) -> IngredientDetail:
    """
    Search the ingredient intelligence engine dictionary using direct or keyword matching.
    Returns structured data for the UI and parser.
    """
    name_clean = name.strip().lower()
    
    # Check exact match
    if name_clean in INGREDIENT_DICTIONARY:
        details = INGREDIENT_DICTIONARY[name_clean]
        return IngredientDetail(name=name, **details)
        
    # Check substring matches
    for key, value in INGREDIENT_DICTIONARY.items():
        if key in name_clean or name_clean in key:
            return IngredientDetail(name=name, **value)
            
    # Default fallback for unrecognized ingredients
    is_additive = "e" in name_clean and any(char.isdigit() for char in name_clean)
    is_preservative = "preservative" in name_clean or "benzoate" in name_clean or "sorbate" in name_clean
    processing_level = 3 if (is_additive or is_preservative) else 2
    
    return IngredientDetail(
        name=name,
        category="Additive" if is_additive else "General Ingredient",
        processing_level=processing_level,
        vegan=True,
        vegetarian=True,
        gluten_free=True,
        safety_notes="Standard ingredient, no major hazard warnings documented.",
        child_suitability=True,
        diabetic_suitability=True,
        gym_suitability=True,
        is_additive=is_additive,
        is_preservative=is_preservative,
        is_controversial=False
    )

def calculate_score(parsed_data: ParsedFoodData, health_mode: str = "General") -> Tuple[int, str, List[ScoreBreakdown], Optional[PersonalizedAdjustment], List[IngredientDetail]]:
    """
    Highly transparent, deterministic scoring engine with dynamic personalization rules.
    Takes parsed ingredients and outputs:
      - score: Calculated health rating (0-100)
      - grade: Standard letter rating (S, A, B, C, D, F)
      - breakdown: Itemized positive and negative score impacts
      - personalized_adjustments: Mode-specific modifications applied
      - ingredient_details: Parsed database information for each ingredient
    """
    score = 100
    breakdown = []
    ingredient_details = []
    
    ingredients = parsed_data.ingredients
    ingredients_str = " ".join(ingredients).lower()
    
    # 1. Map all ingredients to structured database details
    for ing in ingredients:
        detail = analyze_ingredient(ing)
        ingredient_details.append(detail)

    # 2. Base Scoring Rules (Universal Rules)
    
    # Trans Fats / Hydrogenated Oils
    trans_fat_matches = [det.name for det in ingredient_details if "hydrogenated" in det.name or "trans" in det.name]
    if trans_fat_matches:
        penalty = -25
        score += penalty
        breakdown.append(ScoreBreakdown(reason="Contains trans fats / hydrogenated oils", impact=penalty))
        
    # Refined Flour (Maida)
    refined_flour_matches = [det.name for det in ingredient_details if det.category == "Grain / Flour" and det.processing_level == 4]
    if refined_flour_matches:
        penalty = -10
        score += penalty
        breakdown.append(ScoreBreakdown(reason="Contains refined wheat flour (Maida)", impact=penalty))
        
    # Palm Oil / Palmolein
    palm_oil_matches = [det.name for det in ingredient_details if "palm" in det.name]
    if palm_oil_matches:
        penalty = -10
        score += penalty
        breakdown.append(ScoreBreakdown(reason="Contains refined palm oil / palmolein", impact=penalty))
        
    # Added Sugars
    sugar_ingredients = [det.name for det in ingredient_details if det.category == "Sweetener"]
    if sugar_ingredients:
        penalty = -10 if len(sugar_ingredients) == 1 else -20
        score += penalty
        reason = "Contains added sugars" if len(sugar_ingredients) == 1 else "Contains multiple forms of added sugar"
        breakdown.append(ScoreBreakdown(reason=reason, impact=penalty))
        
    # Preservatives
    preservatives = [det.name for det in ingredient_details if det.is_preservative]
    if len(preservatives) > 1:
        penalty = -5
        score += penalty
        breakdown.append(ScoreBreakdown(reason="Contains multiple chemical preservatives", impact=penalty))
        
    # Artificial Colors
    colors = [det.name for det in ingredient_details if det.category == "Color"]
    if colors:
        penalty = -5 * len(colors)
        score += penalty
        breakdown.append(ScoreBreakdown(reason=f"Contains {len(colors)} artificial color(s)", impact=penalty))
        
    # Processing Intensity (NOVA level 4 count)
    ultra_processed_count = sum(1 for det in ingredient_details if det.processing_level == 4)
    if ultra_processed_count > 3:
        penalty = -10
        score += penalty
        breakdown.append(ScoreBreakdown(reason="Highly ultra-processed product", impact=penalty))
    elif len(ingredients) > 15:
        penalty = -5
        score += penalty
        breakdown.append(ScoreBreakdown(reason="Highly processed (long ingredient list)", impact=penalty))

    # Base Positives
    if 0 < len(ingredients) <= 5:
        score += 5
        breakdown.append(ScoreBreakdown(reason="Minimal, simple ingredient list", impact=5))
        
    # First Ingredient is Whole Grain
    if ingredient_details and ingredient_details[0].name in ["whole wheat", "oats", "millet", "ragi", "quinoa", "brown rice", "whole wheat flour"]:
        score += 10
        breakdown.append(ScoreBreakdown(reason="Main ingredient is a premium whole grain", impact=10))

    # Nutrition facts analysis
    nutrition_str = str(parsed_data.nutrition).lower()
    protein_match = re.search(r"protein.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    fiber_match = re.search(r"fiber.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    
    if protein_match and float(protein_match.group(1)) >= 5:
        score += 10
        breakdown.append(ScoreBreakdown(reason="Good source of dietary protein", impact=10))
        
    if fiber_match and float(fiber_match.group(1)) >= 3:
        score += 10
        breakdown.append(ScoreBreakdown(reason="Good source of dietary fiber", impact=10))

    # 3. Apply Personalized Adjustments
    adjustment = None
    
    if health_mode == "Gym/Fitness":
        gym_impact = 0
        gym_reasons = []
        
        # Double protein bonus if high protein
        if protein_match and float(protein_match.group(1)) >= 5:
            gym_impact += 10
            gym_reasons.append("Enhanced bonus for muscle-building protein (+10)")
            
        # Gym specific additions check (e.g. whey protein isolate)
        gym_boosts = [det.name for det in ingredient_details if det.name in ["whey protein isolate", "whey", "peanuts", "almonds", "nuts"]]
        if gym_boosts:
            gym_impact += 10
            gym_reasons.append("Contains highly-rated fitness ingredients (+10)")
            
        # Increased palm oil penalty
        if palm_oil_matches:
            gym_impact -= 5
            gym_reasons.append("Extra penalty for high-saturated fats in fitness mode (-5)")
            
        score += gym_impact
        reason_str = ", ".join(gym_reasons) if gym_reasons else "Active fitness alignment validated."
        adjustment = PersonalizedAdjustment(
            active_mode="Gym/Fitness",
            score_impact=gym_impact,
            reason=f"Gym optimization: {reason_str}"
        )
        
    elif health_mode == "Diabetic Friendly":
        diabetic_impact = 0
        diabetic_reasons = []
        
        # Double refined flour penalty
        if refined_flour_matches:
            diabetic_impact -= 10
            diabetic_reasons.append("Severe penalty for high glycemic refined flour (Maida) (-10)")
            
        # Double added sugars penalty
        if sugar_ingredients:
            diabetic_impact -= 15
            diabetic_reasons.append("Severe penalty for fast-acting added sweeteners (-15)")
            
        score += diabetic_impact
        reason_str = ", ".join(diabetic_reasons) if diabetic_reasons else "Balanced glycemic profile detected."
        adjustment = PersonalizedAdjustment(
            active_mode="Diabetic Friendly",
            score_impact=diabetic_impact,
            reason=f"Diabetic alignment: {reason_str}"
        )
        
    elif health_mode == "Child Friendly":
        child_impact = 0
        child_reasons = []
        
        # Heavy penalty for chemical colors
        if colors:
            penalty = -10 * len(colors)
            child_impact += penalty
            child_reasons.append(f"Synthetic coloring agents warning (-{abs(penalty)})")
            
        # Heavy penalty for chemical preservatives
        if len(preservatives) > 0:
            child_impact -= 10
            child_reasons.append("Heavy preservative loading avoided for children (-10)")
            
        score += child_impact
        reason_str = ", ".join(child_reasons) if child_reasons else "Child-safe clean ingredients confirmed."
        adjustment = PersonalizedAdjustment(
            active_mode="Child Friendly",
            score_impact=child_impact,
            reason=f"Child safety adjustments: {reason_str}"
        )
        
    elif health_mode == "Low Sugar":
        sugar_impact = 0
        if sugar_ingredients:
            sugar_impact = -15
            score += sugar_impact
            adjustment = PersonalizedAdjustment(
                active_mode="Low Sugar",
                score_impact=sugar_impact,
                reason="Aggressive penalty on added sweeteners under Low Sugar restriction."
            )
            
    elif health_mode == "Low Sodium":
        sodium_impact = 0
        if "salt" in ingredients_str or "sodium" in ingredients_str or "preservative" in ingredients_str:
            sodium_impact = -15
            score += sodium_impact
            adjustment = PersonalizedAdjustment(
                active_mode="Low Sodium",
                score_impact=sodium_impact,
                reason="Deduction due to salt / preservative density under Low Sodium profile."
            )
            
    elif health_mode == "Vegetarian":
        non_veg = [det.name for det in ingredient_details if not det.vegetarian]
        if non_veg:
            score = 0
            breakdown.append(ScoreBreakdown(reason=f"CRITICAL WARNING: Contains non-vegetarian items ({', '.join(non_veg)})", impact=-100))
            adjustment = PersonalizedAdjustment(
                active_mode="Vegetarian",
                score_impact=-100,
                reason=f"Failed vegetarian criteria: Contains {', '.join(non_veg)}"
            )
            
    elif health_mode == "Vegan":
        non_vegan = [det.name for det in ingredient_details if not det.vegan]
        if non_vegan:
            score = 0
            breakdown.append(ScoreBreakdown(reason=f"CRITICAL WARNING: Contains animal-derived/dairy items ({', '.join(non_vegan)})", impact=-100))
            adjustment = PersonalizedAdjustment(
                active_mode="Vegan",
                score_impact=-100,
                reason=f"Failed vegan criteria: Contains {', '.join(non_vegan)}"
            )

    # 4. Limit and bounding
    score = max(0, min(100, score))
    
    # Map back the score to letter grade
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
        
    if not breakdown:
        breakdown.append(ScoreBreakdown(reason="Standard ingredients, no major health issues detected.", impact=0))
        
    return score, grade, breakdown, adjustment, ingredient_details

