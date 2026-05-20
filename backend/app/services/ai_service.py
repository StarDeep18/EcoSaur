import json
from app.models.schemas import ParsedFoodData, HomemadeAlternative, ScoreBreakdown, ChatMessage
from google import genai
from google.genai.errors import ClientError
from app.core.config import settings
from typing import List

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Fallback model chain — if one model is rate-limited, try the next
FALLBACK_MODELS = [
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
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
            if e.status_code == 429:
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

async def explain_score(parsed_data: ParsedFoodData, score: int, grade: str, breakdown: List[ScoreBreakdown]) -> str:
    try:
        breakdown_str = ", ".join([f"{b.reason} ({b.impact})" for b in breakdown])
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"A packaged food product received a deterministic score of {score}/100 (Grade {grade}). "
            f"The engine cited these reasons: {breakdown_str}. "
            f"Explain this score in 2 to 3 simple sentences. "
            f"Keep it educational and neutral."
        )
        return _generate_with_fallback(prompt)
    except Exception as e:
        print(f"AI Explanation Error: {e}")
        return "This product's score is based on its ingredient profile. Please review the score breakdown for details."

async def suggest_alternative(parsed_data: ParsedFoodData) -> HomemadeAlternative:
    try:
        ingredients_str = ", ".join(parsed_data.ingredients[:5])
        
        prompt = (
            f"{ECOSAUR_PERSONA}\n\n"
            f"Based on a food containing these main ingredients: {ingredients_str}, "
            f"suggest one simple, healthy, regional Indian homemade alternative. "
            f"If the ingredients are toxic, non-food, or completely unrecognizable as food, "
            f"suggest a standard healthy meal instead and note that the original product seems unsafe. "
            f"Output ONLY a JSON object with 'name' and 'recipe' (under 4 short steps). "
            f"Format exactly like: {{\"name\": \"Baked Masala Wedges\", \"recipe\": \"1. Cut potatoes. 2. Toss with oil. 3. Bake.\"}}"
        )
        result = _generate_with_fallback(prompt)
        json_str = clean_json_response(result)
        data = json.loads(json_str)
        return HomemadeAlternative(
            name=data.get("name", "Homemade Healthy Snack"),
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
