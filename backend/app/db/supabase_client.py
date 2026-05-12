import os
from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    url: str = settings.SUPABASE_URL
    key: str = settings.SUPABASE_KEY
    if not url or not key:
        raise ValueError("Supabase credentials not found in environment")
    return create_client(url, key)
