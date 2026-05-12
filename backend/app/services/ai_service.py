import json
from app.models.schemas import ParsedFoodData, HomemadeAlternative, ScoreBreakdown, ChatMessage
import google.generativeai as genai
from app.core.config import settings
from typing import List

genai.configure(api_key=settings.GEMINI_API_KEY)

# STRICT SYSTEM INSTRUCTIONS (No medical advice, no hallucinated scores)
ECOSAUR_PERSONA = (
    "You are EcoSaur, a friendly, educational food assistant. "
    "RULES: "
    "1. Do NOT give medical advice. If asked, say 'I am an AI assistant, please consult a doctor for medical advice.' "
    "2. Do NOT invent health scores or make fake claims. "
    "3. Keep answers extremely simple, short, and easy to understand. "
    "4. Do NOT attack brands. Focus on the ingredient chemicals."
)

def clean_json_response(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

async def explain_score(parsed_data: ParsedFoodData, score: int, grade: str, breakdown: List[ScoreBreakdown]) -> str:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        breakdown_str = ", ".join([f"{b.reason} ({b.impact})" for b in breakdown])
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"A packaged food product received a deterministic score of {score}/100 (Grade {grade}). "
            f"The engine cited these reasons: {breakdown_str}. "
            f"Explain this score in 2 to 3 simple sentences. "
            f"Keep it educational and neutral."
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"AI Explanation Error: {e}")
        return "This product's score is based on its ingredient profile. Please review the score breakdown for details."

async def suggest_alternative(parsed_data: ParsedFoodData) -> HomemadeAlternative:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        ingredients_str = ", ".join(parsed_data.ingredients[:5])
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"Based on a food containing these main ingredients: {ingredients_str}, "
            f"suggest one simple, healthy, regional Indian homemade alternative. "
            f"Output ONLY a JSON object with 'name' and 'recipe' (under 4 short steps). "
            f"Format exactly like: {{\"name\": \"Baked Masala Wedges\", \"recipe\": \"1. Cut potatoes. 2. Toss with oil. 3. Bake.\"}}"
        )
        response = model.generate_content(prompt)
        json_str = clean_json_response(response.text)
        data = json.loads(json_str)
        return HomemadeAlternative(
            name=data.get("name", "Homemade Healthy Snack"),
            recipe=data.get("recipe", "A simple homemade alternative made with fresh ingredients.")
        )
    except Exception as e:
        print(f"AI Alternative Error: {e}")
        return HomemadeAlternative(
            name="Fresh Fruit or Nuts",
            recipe="Always a safe and healthy alternative to packaged snacks."
        )

async def chat_with_user(ingredients: List[str], history: List[ChatMessage], message: str) -> str:
    """
    Conversational UX layer.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Build the chat context
        ingredients_str = ", ".join(ingredients)
        context = f"{ECOSAUR_PERSONA}\n\nYou are discussing a food product that contains these ingredients: {ingredients_str}.\n"
        
        # Format history for Gemini
        formatted_history = []
        for msg in history[-4:]: # Keep only last 4 messages to save tokens
            formatted_history.append({"role": msg.role, "parts": [{"text": msg.content}]})
            
        chat = model.start_chat(history=formatted_history)
        response = chat.send_message(f"Context: {context}\n\nUser: {message}")
        
        return response.text.strip()
    except Exception as e:
        print(f"AI Chat Error: {e}")
        return "Sorry, I'm having trouble connecting right now. Let's try again later."
