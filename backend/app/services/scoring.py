from app.models.schemas import ParsedFoodData, ScoreBreakdown
from typing import Tuple, List
import re

# Knowledge Base for Deterministic Scoring
SUGAR_ALIASES = ["sugar", "corn syrup", "cane sugar", "maltodextrin", "dextrose", "fructose", "maltose", "sucrose", "honey", "jaggery"]
TRANS_FATS = ["hydrogenated", "partially hydrogenated", "shortening", "margarine"]
REFINED_FLOUR = ["maida", "refined wheat flour", "refined flour", "bleached flour"]
PALM_OIL = ["palm oil", "palmolein", "palm kernel oil"]
PRESERVATIVES = ["benzoate", "sorbate", "propionate", "nitrate", "nitrite", "e200", "e211", "e282", "e250"]
COLORS = ["tartrazine", "sunset yellow", "red 40", "yellow 5", "brilliant blue", "e102", "e110", "e129", "e133"]

def calculate_score(parsed_data: ParsedFoodData) -> Tuple[int, str, List[ScoreBreakdown]]:
    """
    Deterministic rule-based scoring engine.
    AI is NOT used here. Scores are 100% transparent and reproducible.
    """
    score = 100
    breakdown = []
    
    # 1. Ingredient Analysis
    ingredients = parsed_data.ingredients
    ingredients_str = " ".join(ingredients).lower()
    
    # Penalties
    if any(alias in ingredients_str for alias in TRANS_FATS):
        score -= 25
        breakdown.append(ScoreBreakdown(reason="Contains trans fats / hydrogenated oils", impact=-25))
        
    sugar_count = sum(1 for alias in SUGAR_ALIASES if alias in ingredients_str)
    if sugar_count > 0:
        penalty = -10 if sugar_count == 1 else -20
        reason = "Contains added sugars" if sugar_count == 1 else "Contains multiple forms of added sugar"
        score += penalty
        breakdown.append(ScoreBreakdown(reason=reason, impact=penalty))
        
    if any(flour in ingredients_str for flour in REFINED_FLOUR):
        score -= 10
        breakdown.append(ScoreBreakdown(reason="Contains refined flour (Maida)", impact=-10))
        
    if any(oil in ingredients_str for oil in PALM_OIL):
        score -= 10
        breakdown.append(ScoreBreakdown(reason="Contains palm oil", impact=-10))
        
    color_count = sum(1 for color in COLORS if color in ingredients_str)
    if color_count > 0:
        penalty = -5 * color_count
        score += penalty
        breakdown.append(ScoreBreakdown(reason=f"Contains {color_count} artificial color(s)", impact=penalty))
        
    preservative_count = sum(1 for pres in PRESERVATIVES if pres in ingredients_str)
    if preservative_count > 1:
        score -= 5
        breakdown.append(ScoreBreakdown(reason="Contains multiple preservatives", impact=-5))
        
    if len(ingredients) > 15:
        score -= 5
        breakdown.append(ScoreBreakdown(reason="Highly processed (long ingredient list)", impact=-5))

    # Bonuses
    if len(ingredients) > 0 and len(ingredients) <= 5:
        score += 5
        breakdown.append(ScoreBreakdown(reason="Minimal, simple ingredients", impact=5))
        
    # First ingredient check (usually the main component)
    if ingredients and any(whole in ingredients[0] for whole in ["whole wheat", "oats", "millet", "ragi", "quinoa", "brown rice"]):
        score += 10
        breakdown.append(ScoreBreakdown(reason="Main ingredient is a whole grain", impact=10))

    # 2. Nutrition Analysis (if available)
    nutrition_str = str(parsed_data.nutrition).lower()
    
    # Very basic parsing for Protein > 5g
    protein_match = re.search(r"protein.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    if protein_match and float(protein_match.group(1)) >= 5:
        score += 10
        breakdown.append(ScoreBreakdown(reason="Good source of protein", impact=10))
        
    # Basic parsing for Fiber > 3g
    fiber_match = re.search(r"fiber.*?(\d+)(?:\.\d+)?\s*g", nutrition_str)
    if fiber_match and float(fiber_match.group(1)) >= 3:
        score += 10
        breakdown.append(ScoreBreakdown(reason="Good source of dietary fiber", impact=10))

    # Bound score between 0 and 100
    score = max(0, min(100, score))

    # Grade Generator
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

    # Default message if nothing found
    if not breakdown:
        breakdown.append(ScoreBreakdown(reason="Standard ingredients, no major health risks or benefits detected.", impact=0))

    return score, grade, breakdown
