<p align="center">
  <h1 align="center">🦕 EcoSaur</h1>
  <p align="center">
    <strong>Premium AI-Powered Food Ingredient Analyzer</strong><br/>
    <em>Eat Smarter, Not Harder.</em>
  </p>
</p>

---

# Overview

EcoSaur scans packaged food ingredient labels, evaluates nutritional quality using a **transparent, rule-based scoring engine**, and suggests simple homemade alternatives - all without shaming brands or spreading misinformation.

Most food apps scare you. EcoSaur **educates** you.

### Core Principles

| Principle | What it means |
|-----------|---------------|
| 🔍 **Transparent Scoring** | Every point added or deducted is shown with a reason |
| 🤖 **AI Explains, Not Decides** | EcoSaur AI generates explanations - scores are 100% deterministic |
| 🍳 **Actionable Alternatives** | Regional Indian homemade recipes, not generic Western advice |
| 🛡️ **No Fear, No Shame** | Neutral, educational, and scientifically balanced tone - never attacks brands |
| 🛡️ **Scientific Trust** | Explicitly displays OCR and recognized ingredient confidence indices |

---

## Scoring System

EcoSaur uses a **100% deterministic, rule-based scoring engine**. AI never decides scores.

### How It Works

Every product starts at **100 points**. Points are added or deducted based on transparent rules:

#### Penalties

| Trigger | Impact | Example Ingredients |
|---------|--------|---------------------|
| Trans fats / hydrogenated fats | **-30** | Partially hydrogenated vegetable oil, palmolein |
| High sugar load (≥ 15g per serving) | **-15** | Sucrose, sugar, corn syrup |
| Moderate sugar load (5g - 15g) | **-5** | Honey, raw sugar, jaggery |

#### Bonuses

| Trigger | Impact | Example |
|---------|--------|---------|
| High Protein Source (≥ 5g or seeds/whey) | **+10** | Whey protein isolate, milk solids, peanuts |
| High Fiber Source (≥ 3g or whole grains) | **+10** | Whole wheat flour, oats, ragi |

---

# Features

### ✅ Implemented (Premium Consumer-Grade)

- **📱 Expo Mobile Application** - Structured under `mobile/src/` tree (`screens/`, `services/`, `theme/`, `utils/`) built using Expo Router, NativeWind, and Expo Camera for premium ingredient scanning.
- **🔐 Supabase Authentication** - Secure sign-in, signup, and user sessions caching via Expo Router navigation redirects.
- **📷 Ingredient Label Scanner** - Capture ingredient lists via the camera viewfinder with real-time laser overlays.
- **🔤 AI Vision OCR & Correction** - Advanced label text extraction with manual correction and typo spelling normalizers.
- **⚙️ Deterministic Scoring Engine** - Base 100 scoring with letter grades mapping (S, A, B, C, D, F).
- **🌱 Focus Personalization** - Customizable health modes (Diabetic Friendly, Child Friendly, Vegan, Vegetarian) that dynamically adjust scorecards and explanations.
- **🔄 Swipable Indian Swaps** - Healthy regional recipes (e.g. chaas, makhana, semiya) contextualized to your flavor and texture cravings.
- **⚖️ Side-by-Side Comparison** - Compare two products side-by-side with an automated comparative verdict.
- **🗨️ Conversational Chat** - Conversational bot to safely query details on specific chemical E-numbers and stabilizers.
- **🏷️ Barcode Lookup** - Integrated OpenFoodFacts API barcode check with crowdsourced fallback upload logs.
- **📜 Scan History & Limits** - Persisted PostgreSQL scan histories restricted via Supabase Row Level Security (RLS) with a 10 scans/day daily rate-limiting cap.

---

# Tech Stack

### Frontend (Web)
- **Next.js 16** (App Router)
- **TypeScript** & **globals.css** variables

### Mobile (Companion App)
- **Expo 54** (React Native 0.81)
- **Expo Router 6** (File-based navigation)
- **Supabase JS Client** (Auth & Session management)

### Backend
- **FastAPI** (Python 3.11+)
- **SQLAlchemy ORM** (PostgreSQL / SQLite support)
- **Google GenAI SDK** (Gemini Vision OCR, Parser, and Chat)

---

# Architecture

```
┌───────────────────────────────┐     ┌───────────────────────────────┐
│     Next.js Web Frontend      │     │     Expo Mobile Companion     │
│  Upload → OCR → Correct       │     │  Camera → OCR → Correct       │
│  └───► Results & Chat  ◄──────┘     └───────► Results & Chat  ◄─────┘
└──────────────┬────────────────┘             └────────┬──────────────┘
               │                                       │
               └───────────────────┬───────────────────┘
                                   │ HTTP (REST + JWT Bearer)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                            │
│                                                                     │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────┐  │
│  │ OCR Service  │   │  Text Parser    │   │   Scoring Service    │  │
│  │ (AI Vision)  │   │  (Normalization)│   │   (Deterministic)    │  │
│  └──────────────┘   └─────────────────┘   └──────────────────────┘  │
│                                                                     │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────┐  │
│  │  AI Service  │   │ Barcode Service │   │   Supabase Postgres  │  │
│  │  (Explain)   │   │ (OpenFoodFacts) │   │  (RLS Enabled / R/W) │  │
│  └──────────────┘   └─────────────────┘   └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
EcoSaur/
├── backend/
│   ├── src/
│   │   ├── config/
│   │   │   ├── config.py           # Configuration environment setup
│   │   │   ├── database.py         # Multi-DB (Supabase PG / SQLite fallback)
│   │   │   └── migrate.py          # Seeding & DB creation
│   │   ├── db/
│   │   │   └── crud.py             # Database CRUD methods
│   │   ├── middleware/
│   │   │   ├── auth_middleware.py  # Supabase JWT token verification
│   │   │   └── rate_limiter.py     # 10 scans/day limit enforcer
│   │   ├── models/
│   │   │   ├── database_models.py  # SQLAlchemy mapping models
│   │   │   └── schemas.py          # Pydantic typing validations
│   │   ├── routes/
│   │   │   ├── analyze.py          # Scan, compare, barcode endpoints
│   │   │   ├── auth.py             # User profile preferences
│   │   │   └── history.py          # scan history & insights endpoints
│   │   ├── services/
│   │   │   ├── barcode_service.py  # Barcode fetchers
│   │   │   ├── category_engine.py  # Taxonomic classifier
│   │   │   ├── gemini_service.py   # OCR, parsed, explanations & chat
│   │   │   ├── insights_engine.py  # History analyzer
│   │   │   ├── normalization_engine.py # Ingredient spelling mapping
│   │   │   ├── ocr_service.py      # Vision OCR
│   │   │   └── scoring_service.py  # Deterministic score logic
│   │   └── main.py                 # FastAPI application main
│   ├── supabase_setup.sql          # DB setup SQL script
│   └── requirements.txt            # Python dependencies
│
├── mobile/
│   ├── app/                        # Thin routing entrypoints
│   │   ├── _layout.tsx             # Auth listener & route protection
│   │   ├── index.tsx               # Welcome / Dashboard
│   │   ├── login.tsx               # Login redirection
│   │   ├── register.tsx            # Register redirection
│   │   ├── profile.tsx             # User profile redirection
│   │   ├── scan.tsx                # Scanner screen redirect
│   │   ├── correction.tsx          # OCR correction screen redirect
│   │   └── results.tsx             # Results screen redirect
│   ├── src/
│   │   ├── screens/                # Functional Screen Components
│   │   ├── services/               # API & Supabase clients
│   │   ├── theme/                  # Theme constants
│   │   └── utils/                  # Scoring calculations
│
└── README.md                       # You are here
```

---

# Installation

### 1. Database Setup (Supabase)
1. Create a project on [Supabase](https://supabase.com/).
2. Navigate to SQL Editor and execute the query contents from [supabase_setup.sql](file:///c:/Users/Deepak%20S/OneDrive/Desktop/EcoSaur/backend/supabase_setup.sql) to initialize tables and auth triggers.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
Create a `.env` file in the `backend/` directory:
```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_JWT_SECRET=your_supabase_jwt_secret
DATABASE_URL=your_direct_supabase_postgresql_connection_string
```
Start the server:
```bash
uvicorn src.main:app --reload --port 8000
```

### 3. Mobile Setup
```bash
cd ../mobile
npm install
```
Create a `.env` file in the `mobile/` directory:
```env
EXPO_PUBLIC_SUPABASE_URL=your_supabase_url
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
EXPO_PUBLIC_BACKEND_URL=http://localhost:8000/api/v1
```
Start Expo development:
```bash
npm run start
```

---

## Disclaimer

> EcoSaur does **not** provide medical advice. It is an educational tool designed to help users understand food ingredient labels and make informed choices. Always consult a healthcare professional for dietary or medical guidance.
