"""Quick test to check which Gemini models are available under the current API key quota."""
from google import genai
from google.genai.errors import ClientError
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

models = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-1.5-flash']

for m in models:
    try:
        r = client.models.generate_content(model=m, contents="Say hello in one word")
        print(f"✅ SUCCESS with {m}: {r.text.strip()[:50]}")
        break  # Found a working model
    except ClientError as e:
        if e.status_code == 429:
            print(f"⏳ RATE LIMITED {m} (429) — trying next...")
        else:
            print(f"❌ FAILED {m}: {e}")
    except Exception as e:
        print(f"❌ FAILED {m}: {e}")
else:
    print("\n❌ All models exhausted. Your free-tier daily quota is fully used.")
    print("   Options: wait for reset, enable billing, or create a new API key.")
