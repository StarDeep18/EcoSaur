from google import genai
from google.genai import types
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def extract_ingredients_and_nutrition(image_bytes: bytes) -> str:
    """
    Uses Gemini 2.0 Flash to extract raw text from the food label.
    This provides the baseline OCR.
    """
    try:
        prompt = (
            "You are a highly accurate OCR system. Read the attached image of a food package label. "
            "Extract all text exactly as written. Pay special attention to the 'Ingredients' list and the 'Nutrition Facts' panel. "
            "Do not summarize or invent anything. Output ONLY the raw extracted text."
        )
        
        # Gemini expects the image data in a specific format for the API
        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type="image/jpeg",
        )
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[image_part, prompt],
        )
        return response.text.strip()
    except Exception as e:
        # Fallback error message for the UI to handle gracefully
        print(f"OCR Error: {e}")
        return "Error extracting text. Please type the ingredients manually or try another image."
