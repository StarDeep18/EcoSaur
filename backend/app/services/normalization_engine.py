import re
import difflib
from typing import List, Dict, Any, Optional
from app.db import crud

# TRANSLATION INDEX FOR E-NUMBERS
E_NUMBERS = {
    "e211": "sodium benzoate",
    "e202": "potassium sorbate",
    "e102": "tartrazine",
    "e110": "sunset yellow",
    "e621": "monosodium glutamate",
    "e330": "citric acid",
    "e415": "xanthan gum",
    "e322": "soy lecithin",
    "e150d": "caramel color",
    "e500": "sodium bicarbonate"
}

# SYNONYM MAP TO NORMALIZE VARYING CHEMICAL NAMES
SYNONYM_MAP = {
    "hfcs": "corn syrup",
    "high fructose corn syrup": "corn syrup",
    "cane sugar": "sugar",
    "raw sugar": "sugar",
    "white sugar": "sugar",
    "sucrose": "sugar",
    "refined wheat flour": "maida",
    "refined flour": "maida",
    "refined wheat flour (maida)": "maida",
    "all purpose flour": "maida",
    "hydrogenated fat": "hydrogenated vegetable oil",
    "hydrogenated oil": "hydrogenated vegetable oil",
    "palmolein oil": "palmolein",
    "palm oil": "palm oil",
    "msg": "monosodium glutamate",
    "monosodium glutamate (msg)": "monosodium glutamate",
    "table salt": "salt",
    "sodium chloride": "salt",
    "soy lecithin": "soy lecithin",
    "soya lecithin": "soy lecithin",
    "whey protein": "whey protein isolate",
    "curd": "milk solids",
    "yogurt": "milk solids",
    "skimmed milk solids": "milk solids"
}

# INGREDIENT INTELLIGENCE LAYER DATABASE
INGREDIENT_DATABASE = {
    "sugar": {
        "category": "Sweetener",
        "processing_level": 4,
        "additive_type": "Sweetener",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Added simple sweetener. Spikes blood glucose rapidly. Limited consumption is recommended under daily nutritional guidelines.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "corn syrup": {
        "category": "Sweetener",
        "processing_level": 4,
        "additive_type": "Sweetener",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Highly refined fructose syrup. Quick absorption spikes insulin; standard guidelines suggest heavy moderation.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "maltodextrin": {
        "category": "Sweetener/Thickener",
        "processing_level": 4,
        "additive_type": "Thickener",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Refined polysaccharide thickener. Glycemic index is higher than table sugar; diabetic moderation is recommended.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "dextrose": {
        "category": "Sweetener",
        "processing_level": 4,
        "additive_type": "Sweetener",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Simple D-glucose sugar. Rapidly raises blood sugar levels; diabetic moderation is strongly advised.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "jaggery": {
        "category": "Sweetener",
        "processing_level": 2,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Unrefined sugar containing trace iron and minerals. Triggers similar insulin glycemic spikes as white table sugar.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "honey": {
        "category": "Sweetener",
        "processing_level": 1,
        "additive_type": "None",
        "vegan": False,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Natural unrefined floral sweetener. Contains rich enzymes, but acts identical to simple sugar in glycemic response.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "palm oil": {
        "category": "Fat / Oil",
        "processing_level": 4,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Refined saturated oil used for commercial shelf stability. Portion monitoring is standardly advised for lipid balance.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": True
    },
    "palmolein": {
        "category": "Fat / Oil",
        "processing_level": 4,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Liquid fraction of palm oil. Rich in saturated fats; highly common in savory deep-fried snacks for crisp preservation.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": True
    },
    "hydrogenated vegetable oil": {
        "category": "Fat / Oil",
        "processing_level": 4,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Industrial trans fats containing lipids. Saturated structures are synthetically modified; WHO guidelines recommend avoiding trans fats.",
        "child_suitability": False,
        "diabetic_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": True
    },
    "maida": {
        "category": "Grain / Flour",
        "processing_level": 4,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": False,
        "allergy_flags": ["Gluten"],
        "sugar_concern": True,
        "sodium_concern": False,
        "safety_notes": "Refined wheat flour. Starch-heavy base stripped of nutritious bran fiber during industrial milling.",
        "child_suitability": True,
        "diabetic_suitability": False,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "wheat flour": {
        "category": "Grain / Flour",
        "processing_level": 1,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": False,
        "allergy_flags": ["Gluten"],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Whole grain wheat flour (atta). Retains core whole wheat fibers and protein nutrients.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "sodium benzoate": {
        "category": "Preservative",
        "processing_level": 4,
        "additive_type": "Preservative",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": True,
        "safety_notes": "Chemical preservative (E211) used to control bacterial spoilage. Recognized as safe under standard regulatory thresholds.",
        "child_suitability": False,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": True,
        "is_controversial": True
    },
    "potassium sorbate": {
        "category": "Preservative",
        "processing_level": 4,
        "additive_type": "Preservative",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Chemical preservative (E202). Controls mold and yeast growth. standardly safe under regulatory daily bounds.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": True,
        "is_controversial": False
    },
    "tartrazine": {
        "category": "Color",
        "processing_level": 4,
        "additive_type": "Color",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Synthetic yellow dye (E102). Links to hyper-sensitive reactions or minor child hyperactivity are noted under warning thresholds.",
        "child_suitability": False,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "sunset yellow": {
        "category": "Color",
        "processing_level": 4,
        "additive_type": "Color",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Synthetic orange coloring (E110). Linked with sensitivity reactions in hyper-sensitive individuals; portion limits advised.",
        "child_suitability": False,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "gelatin": {
        "category": "Animal Derivative",
        "processing_level": 3,
        "additive_type": "None",
        "vegan": False,
        "vegetarian": False,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Animal collagen derivative. Not compatible with vegetarian or vegan dietary preferences.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "milk solids": {
        "category": "Dairy Product",
        "processing_level": 3,
        "additive_type": "None",
        "vegan": False,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": ["Dairy", "Lactose"],
        "sugar_concern": False,
        "sodium_concern": False,
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
        "additive_type": "None",
        "vegan": False,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": ["Dairy"],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Refined complete milk protein. Highly suitable for muscle repair and daily protein targets.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "monosodium glutamate": {
        "category": "Flavour Enhancer",
        "processing_level": 4,
        "additive_type": "Flavour Enhancer",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": True,
        "safety_notes": "savory flavor enhancer (E621). Standard food additive; safe in standard daily culinary portion limits.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": True
    },
    "salt": {
        "category": "Mineral",
        "processing_level": 2,
        "additive_type": "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": True,
        "safety_notes": "Essential sodium mineral. Saturated dietary salt intakes are programmatically linked to high arterial pressure risks.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": False,
        "is_preservative": False,
        "is_controversial": False
    },
    "citric acid": {
        "category": "Acidulant",
        "processing_level": 2,
        "additive_type": "Acidity Regulator",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Natural acidulant E330. Controls bacterial spoilage and delivers organic tangy profiles.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "xanthan gum": {
        "category": "Emulsifier",
        "processing_level": 4,
        "additive_type": "Thickener",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Starch-fermented binding polysaccharide (E415). Improves mouthfeel and prevents fat-water separations.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "caramel color": {
        "category": "Color",
        "processing_level": 4,
        "additive_type": "Color",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Industrial dark coloring (E150d) produced by heating carbohydrates. Generally safe but highly processed.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    },
    "sodium bicarbonate": {
        "category": "Raising Agent",
        "processing_level": 2,
        "additive_type": "Raising Agent",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": True,
        "safety_notes": "Baking soda (E500). Acts as chemical raising agent to aerate biscuits. Safe but contributes to sodium load.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": True,
        "is_preservative": False,
        "is_controversial": False
    }
}

def clean_token(name: str) -> str:
    """
    Cleans raw ingredients token string by stripping percentage indicators,
    parentheses, mathematical digits, and unwanted characters.
    """
    # E.g. "wheat flour (60%)" -> "wheat flour"
    cleaned = re.sub(r'\(\s*\d+\s*%\s*\)', '', name)
    cleaned = re.sub(r'\d+\s*%', '', cleaned)
    cleaned = cleaned.strip().lower()
    cleaned = cleaned.strip(".,*[]() ")
    return cleaned

def normalize_ingredient(raw_name: str) -> Dict[str, Any]:
    """
    Highly robust multi-stage deterministic ingredient normalization pipeline.
    Order:
      1. Clean raw string
      2. Exact lookups
      3. E-number Translations
      4. Synonym Mappings
      5. Typo-tolerant Fuzzy Matches
      6. Fallback queue tracking for review
    """
    cleaned = clean_token(raw_name)
    
    if not cleaned:
        return get_fallback_intelligence(raw_name)

    # 1. Exact Match
    if cleaned in INGREDIENT_DATABASE:
        return {**INGREDIENT_DATABASE[cleaned], "name": cleaned, "flagged": False}

    # 2. E-Number Translation
    e_match = re.search(r'\b(e\s*\d+\w*)\b', cleaned)
    if e_match:
        e_code = e_match.group(1).replace(" ", "").lower()
        if e_code in E_NUMBERS:
            translated = E_NUMBERS[e_code]
            if translated in INGREDIENT_DATABASE:
                return {**INGREDIENT_DATABASE[translated], "name": translated, "flagged": False, "trans_e_code": e_code}

    # 3. Synonym Mapping
    if cleaned in SYNONYM_MAP:
        mapped = SYNONYM_MAP[cleaned]
        if mapped in INGREDIENT_DATABASE:
            return {**INGREDIENT_DATABASE[mapped], "name": mapped, "flagged": False}

    # 4. Fuzzy Matching (difflib close match)
    matches = difflib.get_close_matches(cleaned, INGREDIENT_DATABASE.keys(), n=1, cutoff=0.72)
    if matches:
        matched_key = matches[0]
        return {**INGREDIENT_DATABASE[matched_key], "name": matched_key, "flagged": False, "original_typo": cleaned}

    # 5. Fallback queue tracking for administrator moderator Moat review
    try:
        crud.queue_unknown_ingredient_standalone(raw_name)
    except Exception as e:
        print(f"Warning: Failed to queue unknown ingredient: {e}")

    return get_fallback_intelligence(raw_name)

def get_fallback_intelligence(name: str) -> Dict[str, Any]:
    """
    Returns a safe fallback structure for unrecognized ingredients,
    ensuring scanning processes NEVER crash.
    """
    norm_name = clean_token(name)
    is_additive = "e" in norm_name and any(char.isdigit() for char in norm_name)
    is_preservative = "preservative" in norm_name or "benzoate" in norm_name or "sorbate" in norm_name
    processing_level = 3 if (is_additive or is_preservative) else 2
    
    return {
        "name": name.strip(),
        "category": "Additive" if is_additive else "Ingredient",
        "processing_level": processing_level,
        "additive_type": "Additive" if is_additive else "None",
        "vegan": True,
        "vegetarian": True,
        "gluten_free": True,
        "allergy_flags": [],
        "sugar_concern": False,
        "sodium_concern": False,
        "safety_notes": "Culinary ingredient. Aligns with standard nutritional daily snacker guidelines.",
        "child_suitability": True,
        "diabetic_suitability": True,
        "is_additive": is_additive,
        "is_preservative": is_preservative,
        "is_controversial": False,
        "flagged": True # Flagged as unknown/low-confidence for inline frontend highlights
    }
