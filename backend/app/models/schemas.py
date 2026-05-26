from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from enum import Enum

class HealthMode(str, Enum):
    GENERAL = "General"
    WEIGHT_LOSS = "Weight Loss"
    GYM_FITNESS = "Gym/Fitness"
    DIABETIC_FRIENDLY = "Diabetic Friendly"
    CHILD_FRIENDLY = "Child Friendly"
    LOW_SUGAR = "Low Sugar"
    LOW_SODIUM = "Low Sodium"
    VEGETARIAN = "Vegetarian"
    VEGAN = "Vegan"

class ExtractedTextResponse(BaseModel):
    raw_text: str

class AnalysisRequest(BaseModel):
    corrected_text: str = Field(..., min_length=5, max_length=5000, description="Corrected OCR text must be between 5 and 5000 characters.")
    product_name: Optional[str] = Field(None, description="Optional name/type of the product, e.g. biscuit, potato chips, etc.")
    user_id: Optional[str] = Field("default", description="Optional user identification for custom preference routing.")

class ParsedFoodData(BaseModel):
    ingredients: List[str]
    nutrition: Dict[str, str]
    product_name: Optional[str] = None

class HomemadeAlternative(BaseModel):
    name: str
    recipe: str
    prep_time_mins: Optional[int] = 15
    approx_cost_inr: Optional[int] = 50

class ScoreBreakdown(BaseModel):
    reason: str
    impact: int

class IngredientDetail(BaseModel):
    name: str
    category: str
    processing_level: int = Field(..., ge=1, le=4, description="NOVA processing level 1-4")
    vegan: bool
    vegetarian: bool
    gluten_free: bool
    safety_notes: Optional[str] = None
    child_suitability: bool
    diabetic_suitability: bool
    gym_suitability: bool
    is_additive: bool
    is_preservative: bool
    is_controversial: bool

class PersonalizedAdjustment(BaseModel):
    active_mode: str
    score_impact: int
    reason: str

class AnalysisResponse(BaseModel):
    score: int
    grade: str
    explanation: str
    alternative: HomemadeAlternative
    breakdown: List[ScoreBreakdown]
    personalized_adjustments: Optional[PersonalizedAdjustment] = None
    ingredient_details: List[IngredientDetail] = []

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

# Product comparison schema models
class ProductComparisonRequest(BaseModel):
    product_names: List[str] = Field(..., description="Names of products to compare.")
    corrected_texts: List[str] = Field(..., description="Ingredient label lists for each product.")
    user_id: Optional[str] = Field("default", description="Optional user preferences identifier.")

class ProductComparisonCard(BaseModel):
    product_name: str
    score: int
    grade: str
    processing_level: str
    additive_density: str
    sugar_level: str
    protein_quality: str
    transparency_index: str
    key_negatives: List[str]
    key_positives: List[str]
    healthy_alternative: str

class ProductComparisonResponse(BaseModel):
    comparison_cards: List[ProductComparisonCard]
    verdict: str


