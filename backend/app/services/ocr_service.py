from google import genai
from google.genai import types
from google.genai.errors import ClientError
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Fallback model chain — if one model is rate-limited, try the next
FALLBACK_MODELS = [
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite',
    'gemini-1.5-flash',
]

async def extract_ingredients_and_nutrition(image_bytes: bytes) -> str:
    """
    Uses Gemini Vision to extract raw text from the food label.
    Automatically falls back to alternate models if rate-limited.
    """
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
    
    last_error = None
    for model in FALLBACK_MODELS:
        try:
            print(f"OCR: Trying model {model}...")
            response = client.models.generate_content(
                model=model,
                contents=[image_part, prompt],
            )
            print(f"OCR: Success with {model}")
            return response.text.strip()
        except ClientError as e:
            last_error = e
            if e.status_code == 429:
                print(f"OCR: {model} rate-limited (429), trying next model...")
                continue
            # Non-rate-limit error — don't retry with other models
            print(f"OCR Error ({model}): {e}")
            break
        except Exception as e:
            last_error = e
            print(f"OCR Error ({model}): {e}")
            break
    
    # All models exhausted or non-retryable error
    print(f"OCR: All models failed. Last error: {last_error}")
    return "Error extracting text. Please type the ingredients manually or try another image."
