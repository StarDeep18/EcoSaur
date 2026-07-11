import json
import re
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from google.genai.errors import ClientError
from src.config.config import settings
from src.models.schemas import ParsedFoodData, HomemadeAlternative, ScoreBreakdown, ChatMessage, NutritionScorecard

# Initialize the Gemini GenAI client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Fallback models hierarchy in case of quota exhaustion
FALLBACK_MODELS = [
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-flash-latest',
    'gemini-flash-lite-latest',
]

ECOSAUR_PERSONA = (
    "You are EcoSaur, a warm, supportive, and trustworthy food companion. "
    "Your tone must be conversational, empathetic, and connecting. Speak like a knowledgeable, caring friend who wants to help, not like a dry AI assistant or chatbot. "
    "Do NOT use generic AI disclaimers such as 'As an AI' or 'Based on my programming'. Instead, connect directly with the user (e.g., 'I know how tough it is to read labels', 'Together we can find a clean alternative'). "
    "RULES: "
    "1. Do NOT give medical advice. If asked, say 'I am here to guide your snack choices, but please consult a doctor for personal medical advice.' "
    "2. Do NOT invent health scores or make fake claims. "
    "3. Keep answers extremely simple, short, supportive, and easy to understand. "
    "4. Do NOT attack brands. Focus neutrally on the ingredients. "
    "5. Avoid fearmongering or alarmist language. Avoid words like 'poison', 'harmful', 'toxic', 'dangerous', or 'avoid completely'. "
    "6. Use balanced, science-grounded, and supportive phrasing (e.g., 'moderation is recommended', 'this option has lower processing which fits standard wellness guidelines')."
)

def _generate_with_fallback(prompt: str) -> str:
    """
    Tries generating content across multiple models.
    Falls back to the next model if the current one is rate-limited (429).
    """
    last_error = None
    for model in FALLBACK_MODELS:
        try:
            print(f"Gemini: Trying model {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            print(f"Gemini: Success with {model}")
            return response.text.strip()
        except ClientError as e:
            last_error = e
            print(f"Gemini ClientError ({model}): {e} — trying next model...")
            continue
        except Exception as e:
            last_error = e
            print(f"Gemini GeneralError ({model}): {e} — trying next model...")
            continue
    
    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

def clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def parse_text(corrected_text: str, user_product_name: Optional[str] = None) -> ParsedFoodData:
    """
    Uses Gemini strictly to parse messy ingredient labels into a structured JSON dictionary.
    No scoring is performed by the LLM.
    """
    try:
        prompt = (
            "Convert the following food label text into a structured JSON object.\n"
            "1. Extract the ingredients into a list of strings.\n"
            "2. Extract the nutrition facts into a dictionary (key: nutrient name, value: amount).\n"
            "3. Deduce the food product category or type (e.g. 'biscuit', 'chips', 'instant noodles', 'chocolate drink', 'cereal') based on the text and ingredients. Return it in the 'product_name' field.\n\n"
            "Output ONLY valid JSON.\n"
            "Format: {\"ingredients\": [\"item1\", \"item2\"], \"nutrition\": {\"protein\": \"5g\", \"sugar\": \"10g\"}, \"product_name\": \"biscuit\"}\n\n"
            f"Text:\n{corrected_text}"
        )
        
        result = _generate_with_fallback(prompt)
        json_str = clean_json_response(result)
        data = json.loads(json_str)
        
        ingredients = data.get("ingredients", [])
        nutrition = data.get("nutrition", {})
        inferred_product_name = data.get("product_name", None)
        
        normalized_ingredients = [str(i).strip().lower() for i in ingredients]
        normalized_nutrition = {str(k).strip().lower(): str(v).strip().lower() for k, v in nutrition.items()}
        
        final_product_name = (user_product_name or inferred_product_name or "snack").strip().lower()
        
        return ParsedFoodData(
            ingredients=normalized_ingredients, 
            nutrition=normalized_nutrition, 
            product_name=final_product_name
        )
    except Exception as e:
        print(f"Parsing Error: {e}")
        return ParsedFoodData(ingredients=[], nutrition={}, product_name=user_product_name or "snack")

async def explain_score(parsed_data: ParsedFoodData, scorecard: NutritionScorecard, breakdown: List[ScoreBreakdown], health_mode: str = "General") -> str:
    """
    Generates a helpful, supportive summary explanation of the nutrition metrics.
    Strictly follows brand-neutral, non-alarmist guidelines.
    """
    try:
        breakdown_str = ", ".join([f"{b.reason}" for b in breakdown])
        scorecard_str = (
            f"NOVA Processing Group: {scorecard.nova_group}, "
            f"Additive Density: {scorecard.additive_density}, "
            f"Sugar Load: {scorecard.sugar_load}, "
            f"Sodium Load: {scorecard.sodium_load}, "
            f"Transparency: {scorecard.transparency_index}"
        )
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"A packaged food product has been analyzed under the user profile focus '{health_mode}'.\n"
            f"Its Nutritional Scorecard: {scorecard_str}.\n"
            f"The analysis highlights: {breakdown_str}.\n\n"
            f"CRITICAL REQUIREMENT:\n"
            f"Explain these metrics in 2 to 3 simple, supportive, and balanced sentences. "
            f"Do NOT use fear-based or alarmist words (avoid: 'harmful', 'toxic', 'dangerous', 'avoid completely'). "
            f"Instead, use calm, evidence-aware, and uncertainty-conscious phrasing (e.g. 'moderation is commonly recommended', 'WHO daily guidelines suggest limiting added simple sweeteners'). "
            f"Keep it educational, neutral, scientific, and constructive."
        )
        return _generate_with_fallback(prompt)
    except Exception as e:
        print(f"AI Explanation Error: {e}")
        return f"This product represents a processed culinary option. Moderation is standardly recommended under a {health_mode} diet. Please review the detailed parameters card."

async def suggest_alternative(parsed_data: ParsedFoodData) -> HomemadeAlternative:
    """
    Generates a direct regional Indian healthy alternative recipe when local database has no match.
    """
    try:
        ingredients_str = ", ".join(parsed_data.ingredients[:5])
        product_name = parsed_data.product_name or "this food item"
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"The user has scanned a food product which is classified as: '{product_name}'. "
            f"It contains these main ingredients: {ingredients_str}.\n\n"
            f"CRITICAL REQUIREMENT:\n"
            f"You MUST suggest a healthy, simple, regional Indian homemade alternative that is of the EXACT SAME food category/type as '{product_name}'.\n\n"
            f"Strict Category Mapping Examples:\n"
            f"- If '{product_name}' is a biscuit, cookie, or rusk: suggest a healthy homemade biscuit/cookie (e.g., Whole Wheat Atta Biscuits, Ragi Cookies, Oats Cookies, or Sesame Whole Wheat Rusk).\n"
            f"- If '{product_name}' is chips, crisps, nachos, or similar snack: suggest healthy homemade chips or dry roasted snacks of that type (e.g., Baked Masala Potato Wedges, Banana Chips, Baked Beetroot Chips, or Roasted Masala Makhana).\n"
            f"- If '{product_name}' is instant noodles, pasta, or vermicelli: suggest healthy homemade noodles or vermicelli (e.g., Whole Wheat Vegetable Noodles, Ragi Semiya Upma, or Homemade Millet Noodles).\n"
            f"- If '{product_name}' is chocolate drink, health drink, or milkshake: suggest a homemade beverage alternative (e.g., Homemade Cocoa Milk, Ragi Malt Health Drink, Badam Milk, or Dry Fruit Milkshake).\n"
            f"- If '{product_name}' is breakfast cereal, granola, or flakes: suggest a healthy breakfast bowl of that type (e.g., Homemade Oats with Honey & Banana, Muesli with Nuts & Seeds, or Roasted Millet Flakes).\n"
            f"- If '{product_name}' is ketchup, sauce, or spread: suggest a fresh homemade chutney or spread (e.g., Fresh Tomato Date Chutney, Mint Coriander Dip, or Homemade Peanut Butter).\n\n"
            f"Do NOT suggest a completely unrelated category of food. The alternative must be a direct homemade equivalent of the scanned snack/food type.\n\n"
            f"Output ONLY a JSON object with 'name' and 'recipe' (under 4 short steps).\n"
            f"Format exactly like: {{\"name\": \"Homemade Whole Wheat Atta Biscuits\", \"recipe\": \"1. Mix atta with a little ghee and jaggery. 2. Shape into cookies. 3. Bake at 180C for 15 mins. 4. Cool and enjoy.\"}}"
        )
        result = _generate_with_fallback(prompt)
        json_str = clean_json_response(result)
        data = json.loads(json_str)
        return HomemadeAlternative(
            name=data.get("name", f"Homemade Healthy {product_name.capitalize()}"),
            recipe=data.get("recipe", "A simple homemade alternative made with fresh ingredients.")
        )
    except Exception as e:
        print(f"AI Alternative Error: {e}")
        return HomemadeAlternative(
            name="Alternative Suggestions Busy",
            recipe="Our custom recipe engine is currently taking a short break. Please check back in a few moments!"
        )

async def chat_with_user(ingredients: List[str], history: List[ChatMessage], message: str) -> str:
    """
    Conversational support explaining ingredients safely and transparently.
    """
    try:
        ingredients_str = ", ".join(ingredients)
        history_text = ""
        for msg in history[-4:]:  # Keep only last 4 messages for context
            role_label = "User" if msg.role == "user" else "Assistant"
            history_text += f"{role_label}: {msg.content}\n"
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"You are discussing a food product that contains these ingredients: {ingredients_str}.\n\n"
            f"Conversation so far:\n{history_text}\n"
            f"User: {message}\n\n"
            f"Respond helpfully and concisely. Keep explanations simple, educational, and positive."
        )
        
        return _generate_with_fallback(prompt)
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "Sorry, I'm having trouble answering right now. Let's try again in a few moments."
