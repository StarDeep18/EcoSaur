from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ExtractedTextResponse(BaseModel):
    raw_text: str

class AnalysisRequest(BaseModel):
    corrected_text: str = Field(..., min_length=5, max_length=5000, description="Corrected OCR text must be between 5 and 5000 characters.")
    product_name: Optional[str] = Field(None, description="Optional name/type of the product, e.g. biscuit, potato chips, etc.")

class ParsedFoodData(BaseModel):
    ingredients: List[str]
    nutrition: Dict[str, str]
    product_name: Optional[str] = None

class HomemadeAlternative(BaseModel):
    name: str
    recipe: str

class ScoreBreakdown(BaseModel):
    reason: str
    impact: int

class AnalysisResponse(BaseModel):
    score: int
    grade: str
    explanation: str
    alternative: HomemadeAlternative
    breakdown: List[ScoreBreakdown]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    ingredients: List[str]
    history: List[ChatMessage]
    message: str

class ChatResponse(BaseModel):
    reply: str

class UserPreferencesRequest(BaseModel):
    health_mode: str = Field(..., description="User health goal mode, e.g. Weight Loss, Gym/Fitness, Diabetic Friendly, Child Friendly, General")

class UserPreferencesResponse(BaseModel):
    id: str
    health_mode: str

