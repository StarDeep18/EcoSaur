<p align="center">
  <h1 align="center">🦕 EcoSaur</h1>
  <p align="center">
    <strong>Premium AI-Powered Food Ingredient Analyzer</strong><br/>
    <em>Eat Smarter, Not Harder.</em>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#api-reference">API</a> •
    <a href="#scoring-system">Scoring</a> •
    <a href="#project-structure">Structure</a> •
    <a href="#roadmap">Roadmap</a>
  </p>
</p>

---

## What is EcoSaur?

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

## Features

### ✅ Implemented (Premium Consumer-Grade)

- **📱 Expo Mobile Application** - Cross-platform React Native companion app built using Expo Router, NativeWind, and Expo Camera for premium on-the-go ingredient scanning and review.
- **📷 Ingredient Label Scanner** - Upload or capture a photo of any food label on both web and mobile clients.
- **🔤 AI Vision OCR** - Advanced text extraction from label images with device-level canvas filtering.
- **✏️ OCR Correction Layer** - Tap-to-correct spelling mistakes manually before running analyses (handles blurry/curved labels).
- **⚡ Spellcheck Loop** - Captures manual spelling correction edits, logging them to improve OCR mapping dynamically.
- **⚙️ Deterministic Scoring Engine** - Multi-dimensional, reproducible health scores (0–100) based strictly on predefined rules.
- **🛡️ Confidence & Trust System** - Displays OCR confidence and dictionary matching rates on results cards for absolute transparency.
- **📊 Score Breakdown** - Transparent table showing exactly why each point was added or deducted.
- **🌱 Multi-Profile Personalization** - Custom scoring adaptations and warnings for goals like Gym/Fitness, Weight Loss, Diabetic Friendly, Child Friendly, Vegan, and Vegetarian.
- **🔬 Intelligent Typo-Tolerant Normalization** - Fuzzy matches text inputs, resolves chemical synonyms, translates E-numbers, and registers unknown ingredients for admin verification.
- **💬 Balanced AI Explanations** - EcoSaur AI explains scores using calm, evidence-aware, non-alarmist scientific language.
- **🍲 Recommendation Reasoning** - Explainable matching system explaining flavor similarity, texture matching, convenience prep times, and processing reductions (NOVA 4 -> Group 1 or 2).
- **🔄 Swipable Alternatives** - Traditional regional Indian recipes suited to the exact snack category (e.g. makhana, chaas, semiya).
- **⚖️ Product Comparison** - Side-by-side smart commercial comparison engine including custom comparison verdicts.
- **🗨️ Conversational UX** - Chat with EcoSaur AI about any ingredient after scan analyses.
- **🏷️ Barcode Scanner** - Permanent crowdsourced database moat lookups with OpenFoodFacts API fail-safes.
- **📜 Scan History Insights** - History dashboard displaying dynamic, non-judgmental behavioral diagnostics (weekly sugar consumption frequency, NOVA 4 ratios, E-number logs, and swap suggestion metrics).
- **🛡️ Community Moderation Queue** - Admin queues to resolve barcode contributions, manage Rollbacks, and verify product uploads.

---

## Tech Stack

### Frontend (Web)

| Technology | Purpose |
|------------|---------|
| [Next.js](https://nextjs.org/) 16 | React framework with App Router |
| [React](https://react.dev/) 19 | UI library |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |

### Mobile (Companion App)

| Technology | Purpose |
|------------|---------|
| [Expo](https://expo.dev/) 54 | Development platform for universal React Native applications |
| [React Native](https://reactnative.dev/) 0.81 | Mobile framework for cross-platform iOS & Android development |
| [Expo Router](https://docs.expo.dev/router/introduction/) 6 | File-based navigation library for React Native |
| [NativeWind](https://www.nativewind.dev/) 4 | Tailwind CSS styling wrapper for native components |

### Backend

| Technology | Purpose |
|------------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | Python API server |
| [SQLite](https://sqlite.org/) | Primary operational database with Write-Ahead Logging (WAL) enabled |
| [SQLAlchemy ORM](https://www.sqlalchemy.org/) | Relational database mapping with migrations and query indexes |
| [EcoSaur AI Vision](https://ai.google.dev/) | Advanced Multimodal OCR, text parsing, explanations, and chat |
| [OpenFoodFacts API](https://world.openfoodfacts.org/) | Barcode product lookup |
| [Pydantic](https://docs.pydantic.dev/) | Request/response validation |

---

## Architecture

```
┌───────────────────────────────┐     ┌───────────────────────────────┐
│     Next.js Web Frontend      │     │     Expo Mobile Companion     │
│  Upload → OCR → Correct       │     │  Camera → OCR → Correct       │
│  └───► Results & Chat  ◄──────┘     └───────► Results & Chat  ◄─────┘
└──────────────┬────────────────┘             └────────┬──────────────┘
               │                                       │
               └───────────────────┬───────────────────┘
                                   │ HTTP (REST)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          FastAPI Backend                            │
│                                                                     │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────┐  │
│  │ OCR Service  │   │  Text Parser    │   │   Scoring Engine     │  │
│  │ (AI Vision)  │   │  (Normalization)│   │   (Rule-Based, 0-100)│  │
│  └──────────────┘   └─────────────────┘   └──────────────────────┘  │
│                                                                     │
│  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────────┐  │
│  │  AI Service  │   │ Barcode Service │   │      SQLite DB       │  │
│  │  (Explain)   │   │ (OpenFoodFacts) │   │  (SQLAlchemy + WAL)  │  │
│  └──────────────┘   └─────────────────┘   └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **AI API Key** - Get one from [Google AI Studio](https://aistudio.google.com/apikey)

### 1. Clone the Repository

```bash
git clone https://github.com/StarDeep18/EcoSaur.git
cd EcoSaur
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
ECOSAUR_AI_API_KEY=your_ai_api_key_here
```

Start the backend server:

```bash
uvicorn app.main:app --reload --port 8000
```

The database tables will be initialized, seeded with taxonomy nodes, and legacy TinyDB history will be auto-migrated dynamically at startup. API docs will be available at `http://localhost:8000/docs`.

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start dev server
npm run dev
```

The app will be available at `http://localhost:3000`.

### 4. Mobile Setup (React Native / Expo Companion)

Ensure you have the Expo Go app installed on your physical device if you wish to run it there.

```bash
cd mobile

# Install dependencies
npm install

# Start the Expo development server
npm run start
```

Press `a` for Android Emulator, `i` for iOS Simulator, or scan the QR code using the Expo Go application on iOS/Android to run it on your physical device.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### `POST /scan/extract`

Upload an image to extract ingredient text via Multimodal AI Vision OCR.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | `UploadFile` | Image file (max 10MB) |

**Response:**
```json
{
  "raw_text": "Ingredients: Wheat flour, Sugar, Palm oil...",
  "low_confidence_words": ["plam", "sger"]
}
```

### `POST /scan/analyze`

Submit corrected text for deterministic scoring, trust index computation, and AI explanation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `corrected_text` | `string` | Corrected OCR text (5–5000 chars) |
| `product_name` | `string` | Optional name of the product |

**Response:**
```json
{
  "scorecard": {
    "nova_group": 4,
    "additive_density": "High",
    "sugar_load": "High",
    "sodium_load": "Low",
    "transparency_index": "Moderate",
    "protein_quality": "Standard",
    "fiber_quality": "Standard"
  },
  "explanation": "This product represents a processed snacker option. WHO guidelines suggest portion moderation...",
  "alternative": {
    "name": "Roasted Spiced Makhana",
    "recipe": "1. Roast makhana. 2. Toss with ghee...",
    "prep_time_mins": 6,
    "approx_cost_inr": 25,
    "reasoning": {
      "why_selected": "Recommended because it matches your preferred salty & spicy flavor...",
      "bullets": [
        "✓ Direct category match for Chips & Crisps",
        "✓ Reduces processing from NOVA 4 to NOVA 2",
        "✓ Under 6 minutes prep time"
      ]
    }
  },
  "breakdown": [
    { "reason": "Product is classified as ultra-processed (NOVA 4)", "impact": -15 },
    { "reason": "Sugar load exceeds 15g per serving", "impact": -15 }
  ],
  "confidence": {
    "ocr_score": 95,
    "ocr_level": "High",
    "match_score": 100,
    "match_level": "High"
  }
}
```

---

## Scoring System

EcoSaur uses a **100% deterministic, rule-based scoring engine**. AI never decides scores.

### How It Works

Every product starts at **100 points**. Points are added or deducted based on transparent rules:

#### Penalties

| Trigger | Impact | Example Ingredients |
|---------|--------|---------------------|
| Trans fats / hydrogenated oils | **-25** | Partially hydrogenated vegetable oil |
| Multiple forms of added sugar | **-20** | Sugar, corn syrup, maltodextrin |
| Single added sugar source | **-10** | Sugar |
| Refined flour (Maida) | **-10** | Refined wheat flour, bleached flour |
| Palm oil | **-10** | Palm oil, palmolein |
| Artificial colors (per color) | **-5 each** | Tartrazine, Sunset Yellow, E110 |
| Multiple preservatives | **-5** | Sodium benzoate + potassium sorbate |
| Long ingredient list (>15) | **-5** | Highly processed products |

#### Bonuses

| Trigger | Impact | Example |
|---------|--------|---------|
| Whole grain as main ingredient | **+10** | Whole wheat flour, oats, ragi |
| Good protein (≥5g) | **+10** | High protein content |
| Good fiber (≥3g) | **+10** | High dietary fiber |
| Simple ingredients (≤5) | **+5** | Minimal processing |

---

## Project Structure

```
EcoSaur/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py        # REST API routes & admin moderation
│   │   ├── core/
│   │   │   └── config.py           # Environment config (Pydantic)
│   │   ├── db/
│   │   │   ├── database.py         # SQLite connector & WAL Mode
│   │   │   ├── migrate.py          # Category seeder & TinyDB migrator
│   │   │   └── tinydb_client.py    # Backward-compatible database adapter
│   │   ├── models/
│   │   │   ├── database_models.py  # SQLAlchemy ORM models
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── ai_service.py       # Explanations, recipes, chat persona
│   │   │   ├── barcode_service.py  # OpenFoodFacts barcode lookup
│   │   │   ├── category_engine.py  # Relational taxonomic classifier
│   │   │   ├── insights_engine.py  # scan history behavior diagnostic
│   │   │   ├── ocr_service.py      # AI Vision OCR extraction
│   │   │   ├── parser.py           # Structuring text → JSON
│   │   │   ├── reasoning_engine.py # explainable matching compiler
│   │   │   └── scoring.py          # ⭐ Deterministic scoring engine
│   │   └── main.py                 # FastAPI app entry point
│   ├── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                # Landing page
│   │   ├── scan/page.tsx           # Scan flow (upload → OCR → correct → results → chat)
│   │   ├── history/page.tsx        # Insights & History dashboard
│   │   ├── layout.tsx              # Root layout
│   │   └── globals.css             # Spacing variables & HSL colors
│
├── mobile/
│   ├── app/
│   │   ├── _layout.tsx             # Universal route wrapper and navigation tabs
│   │   ├── index.tsx               # Dashboard screen with scan logs & goal preferences
│   │   ├── scan.tsx                # Expo camera viewfinder & canvas scanner overlay
│   │   ├── correction.tsx          # Manual text spelling verification layer
│   │   └── results.tsx             # Score details, swipable alternatives & follow-up chat
│   ├── services/
│   │   └── api.ts                  # Axios client hitting FastAPI endpoints
│   ├── utils/
│   │   └── scoring.ts              # Local scoring calculations and helper maps
│   └── package.json                # Expo dependency configuration
│
└── README.md                       # You are here
```

---

## Roadmap

### ✅ Phase 1 & 2 - Premium High-Trust Release (Completed)
- [x] Multimodal AI Vision OCR with device-level preprocessing
- [x] Editable OCR correction layer & manual spellcheck feedback logs
- [x] Deterministic rule-based scoring engine & transparent breakdown
- [x] Explainable suggestion matching detailing craving and texture similarity
- [x] Unified dark-obsidian design system with premium transition motion
- [x] OCR & Ingredient Recognized trust confidence indices
- [x] Non-judgmental Scan History behavioral insights & swap dashboards
- [x] Admin crowdsourcing queues & contributor verification actions
- [x] Supabase/TinyDB systems fully migrated to highly operational SQLite ORM structures under WAL mode
- [x] Fully functional cross-platform Expo / React Native companion app mirroring all core web features

### 🔲 Phase 3 - Community & Mobile Releases
- [ ] iOS App Store & Android Google Play Store publishing pipeline
- [ ] User authentication (OAuth integration)
- [ ] Smart comparison charts across commercial snack brands
- [ ] Gamification (streaks, badges, and community goals)

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is open source. See individual dependency licenses for third-party components.

---

## Disclaimer

> EcoSaur does **not** provide medical advice. It is an educational tool designed to help users understand food ingredient labels and make informed choices. Always consult a healthcare professional for dietary or medical guidance.

---

<p align="center">
  <strong>🦕 EcoSaur - Guide users, don't scare them.</strong>
</p>
