import google.generativeai as genai
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

async def extract_ingredients_and_nutrition(image_bytes: bytes) -> str:
    """
    Uses Gemini 1.5 Flash to extract raw text from the food label.
    This provides the baseline OCR.
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "You are a highly accurate OCR system. Read the attached image of a food package label. "
            "Extract all text exactly as written. Pay special attention to the 'Ingredients' list and the 'Nutrition Facts' panel. "
            "Do not summarize or invent anything. Output ONLY the raw extracted text."
        )
        
        # Gemini expects the image data in a specific format for the API
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_bytes
        }
        
        response = model.generate_content([image_part, prompt])
        return response.text.strip()
    except Exception as e:
        # Fallback error message for the UI to handle gracefully
        print(f"OCR Error: {e}")
        return "Error extracting text. Please type the ingredients manually or try another image."
