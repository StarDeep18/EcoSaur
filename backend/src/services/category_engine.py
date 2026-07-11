from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import re
from google import genai
from src.config.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

from src.models.schemas import ProductCategoryInfo, ComparisonCard

# Supported falling-back models
FALLBACK_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
]

# CURATED DATABASE OF HOMEMADE ALTERNATIVES
CURATED_ALTERNATIVES = [
    # --- CARBONATED BEVERAGES ---
    {
        "name": "Spiced Curd Chaas (Buttermilk)",
        "category": "Beverages",
        "subcategory": "Carbonated Drinks",
        "snack_type": "None",
        "beverage_type": "Dairy-based",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Cold, refreshing, thirst-quenching, savory",
        "convenience_level": 5,
        "processing_level": 1,
        "recipe": "1. Whisk fresh curd (yogurt) with cold water in a 1:2 ratio.\n2. Add finely chopped coriander leaves, a bit of minced green chili, and a pinch of rock salt.\n3. Sprinkle roasted cumin powder (jeera) and mix well.\n4. Serve cold as a gut-healthy, high-protein digestive refreshment.",
        "prep_time_mins": 3,
        "approx_cost_inr": 15
    },
    {
        "name": "Fresh Lime Soda (Nimbu Soda)",
        "category": "Beverages",
        "subcategory": "Carbonated Drinks",
        "snack_type": "None",
        "beverage_type": "Fizzy",
        "flavor_profile": "Sour & Sweet",
        "craving_satisfaction": "Cold, refreshing, fizzy, thirst-quenching",
        "convenience_level": 5,
        "processing_level": 1,
        "recipe": "1. Squeeze half a lime into fresh sparkling carbonated water.\n2. Add a pinch of black salt (kala namak) and roasted cumin powder.\n3. Sweeten with a dash of honey or organic jaggery instead of refined sugar.\n4. Serve chilled over ice cubes for a fizzy, vitamin C-rich natural cooler.",
        "prep_time_mins": 2,
        "approx_cost_inr": 10
    },
    {
        "name": "Traditional Nannari Sherbet",
        "category": "Beverages",
        "subcategory": "Carbonated Drinks",
        "snack_type": "None",
        "beverage_type": "Herbal",
        "flavor_profile": "Sweet",
        "craving_satisfaction": "Cold, sweet, herbal, refreshing",
        "convenience_level": 5,
        "processing_level": 1,
        "recipe": "1. Mix 2 tablespoons of natural nannari (sarsaparilla) root syrup in chilled water.\n2. Add freshly squeezed lime juice.\n3. Stir well with crushed ice.\n4. Enjoy as a traditional body coolant with no synthetic colors or preservatives.",
        "prep_time_mins": 2,
        "approx_cost_inr": 12
    },
    
    # --- CHIPS & CRISPS ---
    {
        "name": "Roasted Ghee Masala Makhana",
        "category": "Snacks",
        "subcategory": "Chips & Crisps",
        "snack_type": "Crunchy",
        "beverage_type": "None",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Crunchy, salty, savory, snackable",
        "convenience_level": 5,
        "processing_level": 2,
        "recipe": "1. Heat a teaspoon of ghee in a heavy pan and add raw makhana (foxnuts).\n2. Roast on low heat until perfectly crunchy (approx 5-7 mins).\n3. Toss in turmeric, red chili powder, chaat masala, and a pinch of rock salt.\n4. Let cool and store in an airtight container for a high-fiber, low-fat alternative.",
        "prep_time_mins": 6,
        "approx_cost_inr": 25
    },
    {
        "name": "Baked Masala Banana Chips",
        "category": "Snacks",
        "subcategory": "Chips & Crisps",
        "snack_type": "Crunchy",
        "beverage_type": "None",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Crunchy, salty, dry snack",
        "convenience_level": 4,
        "processing_level": 2,
        "recipe": "1. Thinly slice raw bananas and soak them in salted water with turmeric.\n2. Drain and pat dry completely.\n3. Toss with a light drizzle of cold-pressed coconut oil.\n4. Bake at 180°C for 15-20 mins (or air-fry) until crisp. Dust with ground black pepper.",
        "prep_time_mins": 25,
        "approx_cost_inr": 20
    },
    {
        "name": "Homemade Air-Fried Potato Wafers",
        "category": "Snacks",
        "subcategory": "Chips & Crisps",
        "snack_type": "Crunchy",
        "beverage_type": "None",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Crunchy, salty, savory, crisp",
        "convenience_level": 4,
        "processing_level": 1,
        "recipe": "1. Slice potatoes paper-thin using a mandoline and soak in cold water.\n2. Drain, dry completely on a towel, and toss with minimal olive oil and sea salt.\n3. Air-fry at 160°C for 12-15 minutes, shaking occasionally until golden crisp.\n4. Sprinkle with a dash of chaat masala.",
        "prep_time_mins": 20,
        "approx_cost_inr": 15
    },

    # --- BISCUITS & COOKIES ---
    {
        "name": "Homemade Oats & Jaggery Cookies",
        "category": "Snacks",
        "subcategory": "Biscuits & Cookies",
        "snack_type": "Crunchy",
        "beverage_type": "None",
        "flavor_profile": "Sweet",
        "craving_satisfaction": "Crunchy, sweet, baked, tea-time partner",
        "convenience_level": 3,
        "processing_level": 2,
        "recipe": "1. Blend rolled oats into a coarse flour.\n2. Mix with whole wheat flour (atta), melted ghee, and powdered jaggery.\n3. Add a splash of milk to bind into a dough, then shape into small cookies.\n4. Bake at 170°C for 12-15 mins. Let cool to get crispy, high-fiber biscuits.",
        "prep_time_mins": 20,
        "approx_cost_inr": 30
    },
    {
        "name": "Baked Ragi & Almond Cookies",
        "category": "Snacks",
        "subcategory": "Biscuits & Cookies",
        "snack_type": "Crunchy",
        "beverage_type": "None",
        "flavor_profile": "Chocolatey",
        "craving_satisfaction": "Crunchy, sweet, chocolatey, rich",
        "convenience_level": 3,
        "processing_level": 2,
        "recipe": "1. Roast ragi (finger millet) flour slightly to remove raw taste.\n2. Cream together butter and jaggery until light.\n3. Mix ragi, whole wheat flour, crushed almonds, and cardamom.\n4. Shape and bake at 180°C for 15 mins for a nutrient-dense calcium-rich cookie.",
        "prep_time_mins": 25,
        "approx_cost_inr": 35
    },

    # --- INSTANT NOODLES ---
    {
        "name": "Vegetable Poha (Flattened Rice)",
        "category": "Snacks",
        "subcategory": "Instant Noodles",
        "snack_type": "Soft",
        "beverage_type": "None",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Warm, savory, filling, quick snack",
        "convenience_level": 4,
        "processing_level": 2,
        "recipe": "1. Rinse thick poha (flattened rice) under water and drain.\n2. Heat mustard oil, add mustard seeds, curry leaves, green chilies, and roasted peanuts.\n3. Sauté finely chopped onions, carrots, and green peas with turmeric.\n4. Mix in poha and salt, steam for 2 mins, and garnish with fresh coriander and lemon.",
        "prep_time_mins": 10,
        "approx_cost_inr": 15
    },
    {
        "name": "Homemade Millet Noodles",
        "category": "Snacks",
        "subcategory": "Instant Noodles",
        "snack_type": "Soft",
        "beverage_type": "None",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Warm, savory, slurpy, noodles craving",
        "convenience_level": 3,
        "processing_level": 2,
        "recipe": "1. Boil store-bought natural multi-millet noodles in water with a drop of oil.\n2. Drain and set aside.\n3. Sauté cabbage, carrots, bell peppers, and spring onions in sesame oil.\n4. Toss the noodles with homemade low-sodium soy sauce, vinegar, and black pepper.",
        "prep_time_mins": 15,
        "approx_cost_inr": 40
    },
    {
        "name": "Vegetable Semiya Upma",
        "category": "Snacks",
        "subcategory": "Instant Noodles",
        "snack_type": "Soft",
        "beverage_type": "None",
        "flavor_profile": "Salty & Spicy",
        "craving_satisfaction": "Warm, savory, soft, comforting",
        "convenience_level": 4,
        "processing_level": 2,
        "recipe": "1. Dry roast vermicelli (semiya) until golden brown.\n2. Heat oil, temper with mustard seeds, chana dal, curry leaves, and ginger.\n3. Sauté mixed green vegetables with turmeric.\n4. Add water, bring to boil, add semiya, cover and cook on low heat until dry.",
        "prep_time_mins": 12,
        "approx_cost_inr": 15
    }
]

def _generate_with_fallback(prompt: str) -> str:
    """Tries generating content across multiple models with fallback logic."""
    last_error = None
    for model in FALLBACK_MODELS:
        try:
            print(f"Classification: Trying model {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            print(f"Classification: Success with {model}")
            return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"Classification Error ({model}): {e}")
            continue
    raise RuntimeError(f"All models failed for classification. Last error: {last_error}")

def classify_product(product_name: str, ingredients: List[str]) -> ProductCategoryInfo:
    """
    Step 1: Heuristic classification matching common keywords.
    Step 2: Fallback to high-speed Gemini classification for precise categorization.
    """
    from src.config.database import SessionLocal
    from src.models.database_models import ProductCategory
    
    name_lower = product_name.lower().strip()
    ingredients_str = " ".join(ingredients).lower()

    db = SessionLocal()
    try:
        categories = db.query(ProductCategory).all()
        
        matched_sub = None
        if any(kw in name_lower for kw in ["cola", "pepsi", "sprite", "fanta", "soda", "carbonated", "soft drink", "mirinda", "beverage", "drink", "thums up"]):
            matched_sub = "Carbonated Drinks"
        elif any(kw in name_lower for kw in ["chip", "crisp", "lays", "bingo", "doritos", "pringles", "kurkure", "makhana", "peanut", "nacho", "wafer", "snack"]):
            matched_sub = "Chips & Crisps"
        elif any(kw in name_lower for kw in ["biscuit", "cookie", "oreo", "bourbon", "digestive", "rusk", "cracker", "britannia", "parle"]):
            matched_sub = "Biscuits & Cookies"
        elif any(kw in name_lower for kw in ["noodle", "maggi", "yippee", "pasta", "ramen", "semiya", "upma", "poha"]):
            matched_sub = "Instant Noodles"
            
        if matched_sub:
            db_cat = db.query(ProductCategory).filter(ProductCategory.subcategory_name == matched_sub).first()
            if db_cat:
                return ProductCategoryInfo(
                    category=db_cat.category_name,
                    subcategory=db_cat.subcategory_name,
                    snack_type=db_cat.snack_type,
                    beverage_type=db_cat.beverage_type,
                    flavor_profile=db_cat.flavor_profile,
                    processing_level=db_cat.processing_level
                )

        # Fast Gemini Classification Fallback
        try:
            valid_cats = list(set([c.category_name for c in categories]))
            valid_subs = list(set([c.subcategory_name for c in categories]))
            
            prompt = (
                "You are a strict food classification algorithm. Classify the following scanned food product.\n"
                f"Product Name: {product_name}\n"
                f"Ingredients list: {ingredients_str}\n\n"
                "TAXONOMY MATRIX RULES:\n"
                f"- 'category' MUST be one of: {valid_cats}\n"
                f"- 'subcategory' MUST be one of: {valid_subs}\n"
                "- If it is a Beverage, 'snack_type' must be 'None', and 'beverage_type' must be one of [Fizzy, Dairy-based, Fruit-based, Herbal].\n"
                "- If it is a Snack/Bakery/Instant Food, 'beverage_type' must be 'None', and 'snack_type' must be one of [Savory, Sweet, Crunchy, Spicy, Soft].\n"
                "- 'flavor_profile' must be one of: [Sweet, Salty & Spicy, Tangy, Sour, Chocolatey, Savory]\n"
                "- 'processing_level' must be an integer between 1 and 4 representing NOVA processing index (most packaged foods are 4).\n\n"
                "Return ONLY a clean JSON object conforming to the rules without markdown formatting.\n"
                "Format: {\"category\": \"Snacks\", \"subcategory\": \"Chips & Crisps\", \"snack_type\": \"Crunchy\", \"beverage_type\": \"None\", \"flavor_profile\": \"Salty & Spicy\", \"processing_level\": 4}"
            )
            response_text = _generate_with_fallback(prompt)
            response_text = response_text.replace("```json", "").replace("```", "").strip()
            import json
            data = json.loads(response_text)
            
            db_cat = db.query(ProductCategory).filter(
                ProductCategory.subcategory_name == data.get("subcategory")
            ).first()
            
            if db_cat:
                return ProductCategoryInfo(
                    category=db_cat.category_name,
                    subcategory=db_cat.subcategory_name,
                    snack_type=db_cat.snack_type,
                    beverage_type=db_cat.beverage_type,
                    flavor_profile=db_cat.flavor_profile,
                    processing_level=db_cat.processing_level
                )
            
            return ProductCategoryInfo(**data)
        except Exception as e:
            print(f"AI Category Classification failed, falling back: {e}")
            is_beverage = any(k in name_lower or k in ingredients_str for k in ["juice", "water", "drink", "milk", "soda", "syrup"])
            fallback_sub = "Carbonated Drinks" if is_beverage else "Chips & Crisps"
            db_cat = db.query(ProductCategory).filter(ProductCategory.subcategory_name == fallback_sub).first()
            if db_cat:
                return ProductCategoryInfo(
                    category=db_cat.category_name,
                    subcategory=db_cat.subcategory_name,
                    snack_type=db_cat.snack_type,
                    beverage_type=db_cat.beverage_type,
                    flavor_profile=db_cat.flavor_profile,
                    processing_level=db_cat.processing_level
                )
            
            return ProductCategoryInfo(
                category="Beverages" if is_beverage else "Snacks",
                subcategory="Carbonated Drinks" if is_beverage else "Chips & Crisps",
                snack_type="None" if is_beverage else "Crunchy",
                beverage_type="Fizzy" if is_beverage else "None",
                flavor_profile="Sweet" if is_beverage else "Salty & Spicy",
                processing_level=4
            )
    finally:
        db.close()

def rank_alternatives(scanned: ProductCategoryInfo) -> List[Dict[str, Any]]:
    """
    Ranks healthy alternatives from our database using contextual similarity scoring.
    """
    from src.config.database import SessionLocal
    from src.models.database_models import Alternative, ProductCategory
    
    db = SessionLocal()
    try:
        alts = db.query(Alternative).join(ProductCategory).all()
        ranked = []

        for alt in alts:
            score = 0
            alt_cat = alt.category
            
            scanned_is_beverage = (scanned.category == "Beverages" or scanned.beverage_type != "None")
            alt_is_beverage = (alt_cat.category_name == "Beverages" or alt_cat.beverage_type != "None")
            
            if scanned_is_beverage != alt_is_beverage:
                continue

            if alt_cat.subcategory_name == scanned.subcategory:
                score += 50

            if alt_cat.flavor_profile == scanned.flavor_profile:
                score += 20

            if scanned.snack_type != "None" and alt_cat.snack_type == scanned.snack_type:
                score += 15
            if scanned.beverage_type != "None" and alt_cat.beverage_type == scanned.beverage_type:
                score += 15

            reduction = max(0, scanned.processing_level - alt_cat.processing_level)
            score += reduction * 5

            if alt_cat.convenience_profile >= 4:
                score += 10

            ranked.append({
                "name": alt.name,
                "recipe": alt.recipe,
                "prep_time_mins": alt.prep_time_mins,
                "approx_cost_inr": alt.approx_cost_inr,
                "score": score
            })

        ranked.sort(key=lambda x: x["score"], reverse=True)
        return ranked
    finally:
        db.close()

def get_comparison_cards(scanned: ProductCategoryInfo, scanned_name: str) -> List[ComparisonCard]:
    """
    Determines 2 commercial healthier products inside the subcategory for comparison.
    """
    sub = scanned.subcategory
    cards = []
    
    if sub == "Carbonated Drinks":
        cards.append(ComparisonCard(
            product_name="Diet Cola / Zero Sugar Soda",
            score=55,
            grade="D",
            nova_group=4,
            sugar_load="Low",
            sodium_load="Low",
            key_negatives=["Contains Artificial Sweeteners (Aspartame/Acesulfame K)", "Contains Phosphoric Acid causing enamel erosion"],
            key_positives=["Zero sugar content", "Zero calorie load"],
            description="A sugar-free commercial alternative. Eliminates insulin spikes, but relies heavily on industrial synthetic sweeteners."
        ))
        cards.append(ComparisonCard(
            product_name="Flavored Sparkling Himalayan Water",
            score=82,
            grade="A",
            nova_group=2,
            sugar_load="Low",
            sodium_load="Low",
            key_negatives=["Contains natural flavor extracts"],
            key_positives=["No added sugars", "No artificial sweeteners", "No synthetic colors", "Highly refreshing"],
            description="Sparkling spring water with zero sweeteners, offering clean fizzy hydration without blood sugar spikes."
        ))
    elif sub == "Chips & Crisps":
        cards.append(ComparisonCard(
            product_name="Commercial Baked Vegetable Chips",
            score=60,
            grade="C",
            nova_group=3,
            sugar_load="Low",
            sodium_load="High",
            key_negatives=["High sodium load", "Often contains palm oil / palmolein for baking"],
            key_positives=["Baked instead of fried", "Higher fiber than regular chips"],
            description="Slightly lower fat commercial alternative, but portion control is still recommended due to high salt content."
        ))
        cards.append(ComparisonCard(
            product_name="Packaged Roasted Salted Makhana",
            score=85,
            grade="A",
            nova_group=2,
            sugar_load="Low",
            sodium_load="Moderate",
            key_negatives=["Moderate added table salt"],
            key_positives=["Rich in fiber and calcium", "Low glycemic index", "Light oil roasting"],
            description="Highly nutritious popped foxnuts offering satisfying crunchiness, rich mineral profiles, and low processing."
        ))
    elif sub == "Biscuits & Cookies":
        cards.append(ComparisonCard(
            product_name="Commercial Digestive Biscuits",
            score=58,
            grade="C",
            nova_group=4,
            sugar_load="Moderate",
            sodium_load="Moderate",
            key_negatives=["Contains refined flour (maida) blends", "Moderate sugar and palm fats"],
            key_positives=["Higher wheat bran fiber content"],
            description="Advertised as healthy, but still ultra-processed containing palm oils and substantial added sugar."
        ))
        cards.append(ComparisonCard(
            product_name="Whole Wheat Atta & Jaggery Cookies",
            score=84,
            grade="A",
            nova_group=2,
            sugar_load="Moderate",
            sodium_load="Low",
            key_negatives=["Natural jaggery sugars"],
            key_positives=["100% whole wheat atta", "No refined sugars", "Baked using pure ghee"],
            description="Traditional whole wheat biscuits prepared without synthetic additives, artificial flavors, or palm oils."
        ))
    elif sub == "Instant Noodles":
        cards.append(ComparisonCard(
            product_name="Commercial Baked Millet Noodles",
            score=65,
            grade="B",
            nova_group=3,
            sugar_load="Low",
            sodium_load="High",
            key_negatives=["High sodium flavor tastemaker packet", "Contains thickeners"],
            key_positives=["Baked (not flash fried in oil)", "Made with nutritious millet flour blend"],
            description="A better commercial alternative which is air-dried. Still contains high salt in the tastemaker."
        ))
        cards.append(ComparisonCard(
            product_name="Organic Whole Wheat Vermicelli (Semiya)",
            score=88,
            grade="A",
            nova_group=1,
            sugar_load="Low",
            sodium_load="Low",
            key_negatives=["Requires kitchen preparation"],
            key_positives=["Unprocessed durum wheat semolina", "Zero sodium", "Zero chemical additives"],
            description="Pure, minimally processed whole wheat vermicelli which forms the basis for healthy, vegetable-rich upma."
        ))
    else:
        cards.append(ComparisonCard(
            product_name=f"Standard Low Sugar {scanned_name}",
            score=62,
            grade="B",
            nova_group=3,
            sugar_load="Low",
            sodium_load="Moderate",
            key_negatives=["Contains mild preservatives"],
            key_positives=["Lower sugar levels", "Standard nutrition profiles"],
            description="A moderately processed commercial alternative focusing on calorie reduction and lower added sweeteners."
        ))
        cards.append(ComparisonCard(
            product_name=f"Traditional Homemade {scanned_name}",
            score=86,
            grade="A",
            nova_group=1,
            sugar_load="Low",
            sodium_load="Low",
            key_negatives=["Zero commercial packaging convenience"],
            key_positives=["100% natural organic ingredients", "Prepared fresh without additives", "Low sodium"],
            description="Made freshly in the kitchen using premium cold-pressed oils, organic grains, and natural seasonings."
        ))
        
    return cards
