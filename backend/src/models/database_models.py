from datetime import datetime, date
import uuid
from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, ForeignKey, Text, Table, Date
from sqlalchemy.orm import relationship
from src.config.database import Base

class User(Base):
    __tablename__ = "profiles"
    
    id = Column(String, primary_key=True, index=True) # UUID from Supabase Auth
    email = Column(String, unique=True, index=True, nullable=False)
    health_mode = Column(String, default="General")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scans = relationship("Scan", back_populates="user", cascade="all, delete-orphan")
    ocr_corrections = relationship("OCRCorrection", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="contributor")
    api_usages = relationship("APIUsage", back_populates="user", cascade="all, delete-orphan")

class ProductCategory(Base):
    __tablename__ = "product_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, index=True, nullable=False)
    subcategory_name = Column(String, index=True, nullable=False)
    parent_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    
    # Taxonomic descriptors
    snack_type = Column(String, default="None")
    beverage_type = Column(String, default="None")
    flavor_profile = Column(String, default="Standard")
    texture_profile = Column(String, default="Standard")
    craving_profile = Column(String, default="Standard")
    convenience_profile = Column(Integer, default=5) # 1-5
    processing_level = Column(Integer, default=4) # NOVA 1-4
    
    # Self-referential relationship
    parent = relationship("ProductCategory", remote_side=[id])
    products = relationship("Product", back_populates="category")
    alternatives = relationship("Alternative", back_populates="category", cascade="all, delete-orphan")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    barcode = Column(String, unique=True, index=True, nullable=False)
    product_name = Column(String, index=True, nullable=False)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=True)
    ingredients_text = Column(Text, nullable=False)
    verified = Column(Boolean, default=False)
    upvotes = Column(Integer, default=0)
    contributor_id = Column(String, ForeignKey("profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("ProductCategory", back_populates="products")
    contributor = relationship("User", back_populates="products")

class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True)
    processing_level = Column(Integer, default=2) # NOVA 1-4
    
    # Intelligence Flags
    vegan = Column(Boolean, default=True)
    vegetarian = Column(Boolean, default=True)
    gluten_free = Column(Boolean, default=True)
    safety_notes = Column(Text, nullable=True)
    child_suitability = Column(Boolean, default=True)
    diabetic_suitability = Column(Boolean, default=True)
    is_additive = Column(Boolean, default=False)
    is_preservative = Column(Boolean, default=False)
    is_controversial = Column(Boolean, default=False)

class Alternative(Base):
    __tablename__ = "alternatives"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    recipe = Column(Text, nullable=False)
    prep_time_mins = Column(Integer, default=15)
    approx_cost_inr = Column(Integer, default=40)
    category_id = Column(Integer, ForeignKey("product_categories.id"), nullable=False)
    
    category = relationship("ProductCategory", back_populates="alternatives")
    recommendation_logs = relationship("RecommendationLog", back_populates="alternative", cascade="all, delete-orphan")

class Scan(Base):
    # This acts as public.scan_history
    __tablename__ = "scan_history"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    date = Column(DateTime, index=True, default=datetime.utcnow)
    corrected_text = Column(Text, nullable=False)
    score = Column(Integer, nullable=False)
    grade = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    
    # Cached alternative details for historical integrity
    alternative_name = Column(String, nullable=True)
    alternative_recipe = Column(Text, nullable=True)
    alternative_prep_time = Column(Integer, nullable=True)
    alternative_cost = Column(Integer, nullable=True)
    
    breakdown_json = Column(Text, nullable=False) # Serialized list of dictionaries
    image_url = Column(Text, nullable=True)
    
    # Trust Metric Confidences
    confidence_ocr = Column(Float, default=1.0)
    confidence_match = Column(Float, default=1.0)
    confidence_analysis = Column(Float, default=1.0)
    confidence_rec = Column(Float, default=1.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="scans")
    recommendation_logs = relationship("RecommendationLog", back_populates="scan", cascade="all, delete-orphan")

class OCRCorrection(Base):
    __tablename__ = "ocr_corrections"
    
    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    product_name = Column(String, nullable=True)
    user_id = Column(String, ForeignKey("profiles.id"), index=True, default="default")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="ocr_corrections")

class ModerationQueue(Base):
    __tablename__ = "moderation_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    item_type = Column(String, index=True, nullable=False) # e.g. "barcode", "ingredient"
    item_id = Column(String, nullable=True)
    item_data_json = Column(Text, nullable=False) # Serialized details of the submission
    status = Column(String, index=True, default="pending") # "pending", "approved", "rejected"
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RecommendationLog(Base):
    __tablename__ = "recommendation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(String, ForeignKey("scan_history.id"), index=True, nullable=False)
    alternative_id = Column(Integer, ForeignKey("alternatives.id"), index=True, nullable=True)
    clicked = Column(Boolean, default=False)
    feedback_thumb = Column(Integer, default=0) # +1 = thumbs up, -1 = thumbs down, 0 = neutral
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scan = relationship("Scan", back_populates="recommendation_logs")
    alternative = relationship("Alternative", back_populates="recommendation_logs")

class APIUsage(Base):
    __tablename__ = "api_usage"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False)
    scan_count = Column(Integer, default=0, nullable=False)
    date = Column(Date, default=date.today, index=True, nullable=False)
    
    user = relationship("User", back_populates="api_usages")
