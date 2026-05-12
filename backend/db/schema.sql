-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY, -- Links to Supabase Auth
    email TEXT UNIQUE NOT NULL,
    health_mode TEXT DEFAULT 'General',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scans/History Table
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    image_url TEXT,
    raw_ocr_text TEXT,
    corrected_text TEXT,
    score INTEGER,
    grade VARCHAR(2),
    ai_explanation TEXT,
    homemade_alternative JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Ingredients Knowledge Base (For deterministic parsing)
CREATE TABLE ingredients_kb (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    category VARCHAR(50), 
    health_impact VARCHAR(20), 
    score_modifier INTEGER 
);
