import json
from app.models.schemas import ParsedFoodData, HomemadeAlternative, ScoreBreakdown, ChatMessage
from google import genai
from google.genai.errors import ClientError
from app.core.config import settings
from typing import List

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Fallback model chain — if one model is rate-limited, try the next
FALLBACK_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
]

# STRICT SYSTEM INSTRUCTIONS (No medical advice, no hallucinated scores)
ECOSAUR_PERSONA = (
    "You are EcoSaur, a friendly, educational food assistant. "
    "RULES: "
    "1. Do NOT give medical advice. If asked, say 'I am an AI assistant, please consult a doctor for medical advice.' "
    "2. Do NOT invent health scores or make fake claims. "
    "3. Keep answers extremely simple, short, and easy to understand. "
    "4. Do NOT attack brands. Focus on the ingredient chemicals."
)

def _generate_with_fallback(prompt: str) -> str:
    """
    Tries generating content across multiple models.
    Falls back to the next model if the current one is rate-limited (429).
    """
    last_error = None
    for model in FALLBACK_MODELS:
        try:
            print(f"AI: Trying model {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            print(f"AI: Success with {model}")
            return response.text.strip()
        except ClientError as e:
            last_error = e
            if e.code == 429:
                print(f"AI: {model} rate-limited (429), trying next model...")
                continue
            print(f"AI Error ({model}): {e}")
            break
        except Exception as e:
            last_error = e
            print(f"AI Error ({model}): {e}")
            break
    
    raise RuntimeError(f"All models failed. Last error: {last_error}")

def clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def explain_score(parsed_data: ParsedFoodData, score: int, grade: str, breakdown: List[ScoreBreakdown], health_mode: str = "General") -> str:
    try:
        breakdown_str = ", ".join([f"{b.reason} ({b.impact})" for b in breakdown])
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"A packaged food product received a deterministic score of {score}/100 (Grade {grade}) under the active user health profile: '{health_mode}'. "
            f"The engine cited these reasons: {breakdown_str}. "
            f"Explain this score in 2 to 3 simple, friendly sentences. Specifically discuss how this product impacts the user's '{health_mode}' goal (e.g. why added sugar drops the grade heavily for a diabetic focus, or why high protein is excellent for a fitness focus). "
            f"Keep it educational, neutral, and practical."
        )
        return _generate_with_fallback(prompt)
    except Exception as e:
        print(f"AI Explanation Error: {e}")
        return f"This product's score is {score}/100 (Grade {grade}) under your {health_mode} preference. Please review the score breakdown for more details."

async def suggest_alternative(parsed_data: ParsedFoodData) -> HomemadeAlternative:
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
            f"Do NOT suggest a completely unrelated category of food (e.g. do not suggest khichdi, poha, or chana if the original product is a biscuit or potato chips). The alternative must be a direct homemade equivalent of the scanned snack/food type.\n\n"
            f"If the ingredients are toxic, non-food, or completely unrecognizable, suggest a safe homemade version of that category and note any safety concerns.\n\n"
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
            name="AI Assistant Busy",
            recipe="Our AI is currently taking a short break (rate limit). Please try again in a few moments for a custom recipe!"
        )

async def chat_with_user(ingredients: List[str], history: List[ChatMessage], message: str) -> str:
    """
    Conversational UX layer.
    """
    try:
        # Build the chat context
        ingredients_str = ", ".join(ingredients)
        
        # Build full conversation as a single prompt with history context
        history_text = ""
        for msg in history[-4:]:  # Keep only last 4 messages to save tokens
            role_label = "User" if msg.role == "user" else "Assistant"
            history_text += f"{role_label}: {msg.content}\n"
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"You are discussing a food product that contains these ingredients: {ingredients_str}.\n\n"
            f"Conversation so far:\n{history_text}\n"
            f"User: {message}\n\n"
            f"Respond helpfully and concisely."
        )
        
        return _generate_with_fallback(prompt)
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "Sorry, I'm having trouble connecting right now. Let's try again later."
