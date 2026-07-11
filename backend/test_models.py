from google import genai
from src.config.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
try:
    print("Listing models...")
    for model in client.models.list():
        print(f"Name: {model.name}")
except Exception as e:
    print(f"Failed to list models: {e}")
