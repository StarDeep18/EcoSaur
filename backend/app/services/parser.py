import json
import google.generativeai as genai
from app.models.schemas import ParsedFoodData
from app.core.config import settings
import re

genai.configure(api_key=settings.GEMINI_API_KEY)

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

def parse_text(corrected_text: str) -> ParsedFoodData:
    """
    Uses Gemini STRICTLY as a structural parser to convert messy text into JSON.
    This does NO scoring or evaluation.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            "Convert the following food label text into a structured JSON object. "
            "Extract the ingredients into a list of strings. "
            "Extract the nutrition facts into a dictionary (key: nutrient name, value: amount). "
            "Output ONLY valid JSON. "
            "Format: {\"ingredients\": [\"item1\", \"item2\"], \"nutrition\": {\"protein\": \"5g\", \"sugar\": \"10g\"}}\n\n"
            f"Text:\n{corrected_text}"
        )
        
        response = model.generate_content(prompt)
        json_str = clean_json_response(response.text)
        data = json.loads(json_str)
        
        ingredients = data.get("ingredients", [])
        nutrition = data.get("nutrition", {})
        
        # Simple normalization: strip whitespace and lowercase for easier scoring
        normalized_ingredients = [str(i).strip().lower() for i in ingredients]
        normalized_nutrition = {str(k).strip().lower(): str(v).strip().lower() for k, v in nutrition.items()}
        
        return ParsedFoodData(ingredients=normalized_ingredients, nutrition=normalized_nutrition)
    except Exception as e:
        print(f"Parsing Error: {e}")
        # Fallback to empty if parsing fails
        return ParsedFoodData(ingredients=[], nutrition={})
