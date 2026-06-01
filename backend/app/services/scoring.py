from app.models.schemas import ParsedFoodData, ScoreBreakdown, IngredientDetail, PersonalizedAdjustment, NutritionScorecard
from typing import Tuple, List, Optional, Dict, Any
import re
import difflib

# Comprehensive Dictionary for Structured Ingredient Intelligence
INGREDIENT_DICTIONARY = {
    "sugar": {
        "category": "Sweetener",
        "processing_level": 4,
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "safety_notes": "Added sweetener. Spikes insulin and blood glucose levels; moderation is commonly recommended by dietitians.",
        "child_suitability": False,
        "diabetic_suitability": False,
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
        "safety_notes": "Simple sweetener extracted from sugar cane. Moderation is commonly recommended under standard daily energy guidelines.",
        "child_suitability": False,
        "diabetic_suitability": False,
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
        "safety_notes": "Refined sweetener syrup. High glycemic index; modern guidelines advise limiting consumption in daily snacks.",
        "child_suitability": False,
        "diabetic_suitability": False,
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
        "safety_notes": "Processed starch with a glycemic index higher than table sugar. Quickly digested; diabetic moderation is recommended.",
        "child_suitability": False,
        "diabetic_suitability": False,
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
        "safety_notes": "Simple sugar structurally identical to glucose. Rapidly raises blood glucose; moderation is advised.",
        "child_suitability": False,
        "diabetic_suitability": False,
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
        "safety_notes": "Unrefined sugar containing trace minerals. Triggers glycemic spikes like refined sugars, but lacks synthetic chemicals.",
        "child_suitability": True,
        "diabetic_suitability": False,
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
        "safety_notes": "Natural sweetener produced by bees. Acts as a simple sugar in the body; portion control is commonly advised.",
        "child_suitability": True,
        "diabetic_suitability": False,
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
        "safety_notes": "Saturated fat. Widely used for shelf stability in commercial packaging. Moderation is commonly recommended for cardiovascular balance.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "Liquid component of palm oil. Rich in saturated fats; highly common in Indian packaged snacks to preserve crispness.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "Processed oil containing industrial trans fats. Saturated fats are structurally modified; modern health guidelines recommend avoiding trans fats.",
        "child_suitability": False,
        "diabetic_suitability": False,
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
        "safety_notes": "Refined wheat flour. Natural dietary fiber and wheat bran are stripped during industrial milling.",
        "child_suitability": True,
        "diabetic_suitability": False,
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
        "safety_notes": "Maida flour. Refined simple starch stripped of complex grain nutrients.",
        "child_suitability": True,
        "diabetic_suitability": False,
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
        "safety_notes": "Chemical preservative (E211) used to control bacterial spoilage. Generally recognized as safe within standard regulator guidelines.",
        "child_suitability": False,
        "diabetic_suitability": True,
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
        "safety_notes": "Common preservative (E202) used to prevent mold and yeast growth. Portions are standardly restricted to preserve freshness.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "Synthetic food dye (E102). Some research indicates sensitivity or minor hyperactivity trends in children; moderation is advised.",
        "child_suitability": False,
        "diabetic_suitability": True,
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
        "safety_notes": "Synthetic orange food coloring (E110). Linked with sensitivity reactions in hyper-sensitive individuals; portion limits advised.",
        "child_suitability": False,
        "diabetic_suitability": True,
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
        "safety_notes": "Collagen derivative obtained from animal raw materials. Not compatible with vegetarian or vegan dietary preferences.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "Dry dairy components containing natural lactose. Source of calcium, but not compatible with vegan guidelines.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "Refined milk protein. Highly suitable for dietary protein needs and active physical fitness routines.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "MSG (E621). Standard savory flavor enhancer. Widely recognized as safe in controlled portions by food authorities.",
        "child_suitability": True,
        "diabetic_suitability": True,
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
        "safety_notes": "Essential mineral. Excessive sodium intake is commonly linked to elevated blood pressure risks; moderation is advised.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    }
}

from app.services import normalization_engine

# Sub-millisecond Typo-Tolerant Normalizer helper
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

def calculate_score(parsed_data: ParsedFoodData, health_mode: str = "General") -> Tuple[NutritionScorecard, List[ScoreBreakdown], Optional[PersonalizedAdjustment], List[IngredientDetail]]:
    """
    Startup-focused evidence-aware scoring engine. Calculates multi-dimensional
    NutritionScorecard parameters to replace simple binary grades.
    """
    ingredient_details = []
    breakdown = []
    
    ingredients = parsed_data.ingredients
    ingredients_str = " ".join(ingredients).lower()
    
    # 1. Standardize and look up ingredients
    for ing in ingredients:
        detail = analyze_ingredient(ing)
        ingredient_details.append(detail)
        
    # 2. Compute Multi-Dimensional Parameters
    
    # NOVA processing index (Max NOVA processing level among ingredients)
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
    
    if sugar_match:
        sugar_val = float(sugar_match.group(1))
        if sugar_val >= 15:
            sugar_load = "High"
        elif sugar_val >= 5:
            sugar_load = "Moderate"
        else:
            sugar_load = "Low"
    else:
        # Fallback based on sweetener count
        sweetener_count = sum(1 for det in ingredient_details if det.category == "Sweetener")
        if sweetener_count > 1:
            sugar_load = "High"
        elif sweetener_count == 1:
            sugar_load = "Moderate"
        else:
            sugar_load = "Low"
            
    # Sodium Load
    sodium_match = re.search(r"sodium.*?(\d+)(?:\.\d+)?\s*m?g", nutrition_str)
    if sodium_match:
        sodium_val = float(sodium_match.group(1))
        if sodium_val >= 400:
            sodium_load = "High"
        elif sodium_val >= 100:
            sodium_load = "Moderate"
        else:
            sodium_load = "Low"
    else:
        # Fallback on salt presence
        salt_count = sum(1 for det in ingredient_details if "salt" in det.name or "sodium" in det.name)
        if salt_count > 1 or "potassium sorbate" in ingredients_str or "sodium benzoate" in ingredients_str:
            sodium_load = "High"
        elif salt_count == 1:
            sodium_load = "Moderate"
        else:
            sodium_load = "Low"
            
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
    if (protein_match and float(protein_match.group(1)) >= 5) or has_protein_source:
        protein_quality = "High Source"
    else:
        protein_quality = "Standard"
        
    # Fiber Quality
    fiber_match = re.search(r"fiber.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    has_fiber_source = any(d.name in ["whole wheat", "oats", "millet", "ragi", "quinoa", "brown rice", "whole wheat flour"] for d in ingredient_details)
    if (fiber_match and float(fiber_match.group(1)) >= 3) or has_fiber_source:
        fiber_quality = "High Source"
    else:
        fiber_quality = "Standard"
        
    scorecard = NutritionScorecard(
        nova_group=nova_group,
        additive_density=additive_density,
        sugar_load=sugar_load,
        sodium_load=sodium_load,
        transparency_index=transparency_index,
        protein_quality=protein_quality,
        fiber_quality=fiber_quality
    )

    # 3. Create Objective, Balanced Breakdowns (Deductions as reference)
    if nova_group == 4:
        breakdown.append(ScoreBreakdown(reason="Product is classified as ultra-processed (NOVA 4) due to refined base processing", impact=-15))
    if additive_density == "High":
        breakdown.append(ScoreBreakdown(reason="Contains multiple additives; food regulations recognize these as safe in portion moderation", impact=-10))
    if sugar_load == "High":
        breakdown.append(ScoreBreakdown(reason="Sugar load exceeds 15g per serving; daily guidelines suggest limiting added simple sweeteners", impact=-15))
    if sodium_load == "High":
        breakdown.append(ScoreBreakdown(reason="High sodium density; portion monitoring is commonly recommended for arterial pressure balance", impact=-10))
    if protein_quality == "High Source":
        breakdown.append(ScoreBreakdown(reason="Includes a high-quality source of dietary protein", impact=10))
    if fiber_quality == "High Source":
        breakdown.append(ScoreBreakdown(reason="Includes complex whole grains contributing to fiber intake", impact=10))

    if not breakdown:
        breakdown.append(ScoreBreakdown(reason="Standard nutritional profile; aligns with standard daily snack balance guidelines", impact=0))

    # 4. Personalization Adjustments (Objective Warning alerts)
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
            scorecard.nova_group = 4 # Demote due to incompatibility
            adjustment = PersonalizedAdjustment(
                active_mode="Vegetarian",
                reason=f"Failed vegetarian criteria: Contains animal-derived gelatin/broths ({', '.join(non_veg)})"
            )
            
    elif health_mode == "Vegan":
        non_vegan = [det.name for det in ingredient_details if not det.vegan]
        if non_vegan:
            scorecard.nova_group = 4
            adjustment = PersonalizedAdjustment(
                active_mode="Vegan",
                reason=f"Failed vegan criteria: Contains dairy or animal-derived ingredients ({', '.join(non_vegan)})"
            )

    return scorecard, breakdown, adjustment, ingredient_details


