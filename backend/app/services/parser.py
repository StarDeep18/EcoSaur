import json
from google import genai
from app.models.schemas import ParsedFoodData
from app.core.config import settings
import re

client = genai.Client(api_key=settings.GEMINI_API_KEY)

def clean_json_response(text: str) -> str:
    """Removes markdown formatting from LLM JSON response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

from typing import Optional

FALLBACK_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
]

def _generate_with_fallback(prompt: str) -> str:
    from google.genai.errors import ClientError
    last_error = None
    for model in FALLBACK_MODELS:
        try:
            print(f"Parser: Trying model {model}...")
            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )
            print(f"Parser: Success with {model}")
            return response.text.strip()
        except ClientError as e:
            last_error = e
            if e.code == 429:
                print(f"Parser: {model} rate-limited (429), trying next model...")
                continue
            print(f"Parser Error ({model}): {e}")
            break
        except Exception as e:
            last_error = e
            print(f"Parser Error ({model}): {e}")
            break
    
    raise RuntimeError(f"All models failed. Last error: {last_error}")

def parse_text(corrected_text: str, user_product_name: Optional[str] = None) -> ParsedFoodData:
    """
    Uses Gemini STRICTLY as a structural parser to convert messy text into JSON.
    This does NO scoring or evaluation.
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
        
        # Simple normalization: strip whitespace and lowercase for easier scoring
        normalized_ingredients = [str(i).strip().lower() for i in ingredients]
        normalized_nutrition = {str(k).strip().lower(): str(v).strip().lower() for k, v in nutrition.items()}
        
        # Priority: User input > inferred from text > default fallback
        final_product_name = (user_product_name or inferred_product_name or "snack").strip().lower()
        
        return ParsedFoodData(
            ingredients=normalized_ingredients, 
            nutrition=normalized_nutrition, 
            product_name=final_product_name
        )
    except Exception as e:
        print(f"Parsing Error: {e}")
        # Fallback to empty if parsing fails
        return ParsedFoodData(ingredients=[], nutrition={}, product_name=user_product_name or "snack")
