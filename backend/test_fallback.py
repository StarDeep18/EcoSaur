"""Quick test to check which Gemini models are available under the current API key quota."""
from google import genai
from google.genai.errors import ClientError
from src.config.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
print(f"Loaded API Key: {settings.GEMINI_API_KEY[:10]}...{settings.GEMINI_API_KEY[-5:] if settings.GEMINI_API_KEY else ''}")

models = ['gemini-2.0-flash', 'gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-pro-latest']

for m in models:
    try:
        r = client.models.generate_content(model=m, contents="Say hello in one word")
        print(f"[SUCCESS] with {m}: {r.text.strip()[:50]}")
        break  # Found a working model
    except ClientError as e:
        if e.code == 429:
            print(f"[RATE LIMITED] {m} (429): {e} - trying next...")
        else:
            print(f"[FAILED] {m}: {e}")
    except Exception as e:
        print(f"[FAILED] {m}: {e}")
else:
    print("\n[ALL MODELS EXHAUSTED] Your free-tier daily quota is fully used.")
    print("   Options: wait for reset, enable billing, or create a new API key.")
