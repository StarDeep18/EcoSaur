<p align="center">
  <h1 align="center">🦕 EcoSaur</h1>
  <p align="center">
    <strong>AI-Powered Food Ingredient Analyzer</strong><br/>
    <em>Eat Smarter, Not Harder.</em>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#api-reference">API</a> •
    <a href="#scoring-system">Scoring</a> •
    <a href="#roadmap">Roadmap</a>
  </p>
</p>

---

## What is EcoSaur?

EcoSaur scans packaged food ingredient labels, evaluates nutritional quality using a **transparent, rule-based scoring engine**, and suggests simple homemade alternatives — all without shaming brands or spreading misinformation.

Most food apps scare you. EcoSaur **educates** you.

### Core Principles

| Principle | What it means |
|-----------|---------------|
| 🔍 **Transparent Scoring** | Every point added or deducted is shown with a reason |
| 🤖 **AI Explains, Not Decides** | Gemini generates explanations — scores are 100% deterministic |
| 🍳 **Actionable Alternatives** | Regional Indian homemade recipes, not generic Western advice |
| 🛡️ **No Fear, No Shame** | Neutral, educational tone — never attacks brands |

---

## Features

### ✅ Implemented (MVP)

- **📷 Ingredient Label Scanner** — Upload or capture a photo of any food label
- **🔤 Gemini Vision OCR** — AI-powered text extraction from label images
- **✏️ OCR Correction Layer** — Edit extracted text before analysis (handles blurry/curved labels)
- **⚙️ Rule-Based Scoring Engine** — Deterministic, reproducible health scores (0–100)
- **📊 Score Breakdown** — Transparent table showing exactly why each point was added or deducted
- **💬 AI Explanations** — Gemini explains the score in simple, neutral language
- **🍲 Homemade Alternatives** — Regional Indian recipe suggestions powered by AI
- **🗨️ Conversational UX** — Chat with EcoSaur about any ingredient after analysis
- **🏷️ Barcode Scanner** — Look up products via OpenFoodFacts API
- **📜 Scan History** — Local storage-based history of past analyses

---

## Tech Stack

### Frontend

| Technology | Purpose |
|------------|---------|
| [Next.js](https://nextjs.org/) 16 | React framework with App Router |
| [React](https://react.dev/) 19 | UI library |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |

### Backend

| Technology | Purpose |
|------------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | Python API server |
| [Gemini 1.5 Flash](https://ai.google.dev/) | OCR, text parsing, explanations, chat |
| [Supabase](https://supabase.com/) | Database (PostgreSQL) |
| [OpenFoodFacts API](https://world.openfoodfacts.org/) | Barcode product lookup |
| [Pydantic](https://docs.pydantic.dev/) | Request/response validation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                        │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Upload   │→│  OCR      │→│ Correction│→│  Results   │  │
│  │  Screen   │  │  Extract  │  │  Screen   │  │  + Chat   │  │
│  └──────────┘  └───────────┘  └──────────┘  └───────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP (REST)
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ OCR Service  │  │ Text Parser  │  │  Scoring Engine    │  │
│  │ (Gemini      │  │ (Gemini →    │  │  (100% Rule-Based, │  │
│  │  Vision)     │  │  Structured  │  │   No AI)           │  │
│  │             │  │  JSON)       │  │                    │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────┐  │
│  │ AI Service   │  │ Barcode      │  │  Supabase DB       │  │
│  │ (Explain,    │  │ Service      │  │  (Users, Scans,    │  │
│  │  Recipes,    │  │ (OpenFood    │  │   Ingredients KB)  │  │
│  │  Chat)       │  │  Facts)      │  │                    │  │
│  └─────────────┘  └──────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **Gemini API Key** — Get one from [Google AI Studio](https://aistudio.google.com/apikey)
- **Supabase Project** *(optional for MVP)* — [supabase.com](https://supabase.com)

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
GEMINI_API_KEY=your_gemini_api_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

Start the backend server:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

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

### 4. Database Setup (Optional)

Run the schema in your Supabase SQL editor:

```sql
-- Located at backend/db/schema.sql
-- Creates: users, scans, ingredients_kb tables
```

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

### `POST /scan/extract`

Upload an image to extract ingredient text via Gemini Vision OCR.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file` | `UploadFile` | Image file (max 10MB) |

**Response:**
```json
{
  "raw_text": "Ingredients: Wheat flour, Sugar, Palm oil..."
}
```

### `POST /scan/analyze`

Submit corrected text for deterministic scoring + AI explanation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `corrected_text` | `string` | Corrected OCR text (5–5000 chars) |

**Response:**
```json
{
  "score": 65,
  "grade": "C",
  "explanation": "This product contains added sugars and refined flour...",
  "alternative": {
    "name": "Homemade Ragi Cookies",
    "recipe": "1. Mix ragi flour with jaggery..."
  },
  "breakdown": [
    { "reason": "Contains added sugars", "impact": -10 },
    { "reason": "Contains refined flour (Maida)", "impact": -10 },
    { "reason": "Good source of protein", "impact": 10 }
  ]
}
```

### `POST /scan/chat`

Conversational follow-up about ingredients.

| Parameter | Type | Description |
|-----------|------|-------------|
| `ingredients` | `string[]` | Ingredient list for context |
| `history` | `ChatMessage[]` | Previous messages |
| `message` | `string` | User's question |

**Response:**
```json
{
  "reply": "Maltodextrin is a starch-derived food additive..."
}
```

### `GET /scan/barcode/{barcode}`

Look up a product by barcode via OpenFoodFacts.

**Response:**
```json
{
  "raw_text": "Carbonated Water, Sugar, Colour (Caramel E150d)..."
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

### Grade Scale

| Score | Grade | Meaning |
|-------|-------|---------|
| 90–100 | **S** | Excellent nutritional quality |
| 80–89 | **A** | Very good |
| 70–79 | **B** | Good |
| 60–69 | **C** | Moderate |
| 40–59 | **D** | Poor |
| 0–39 | **F** | Worst nutritional quality |

---

## Project Structure

```
EcoSaur/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py        # REST API routes
│   │   ├── core/
│   │   │   └── config.py           # Environment config (Pydantic)
│   │   ├── db/
│   │   │   └── supabase_client.py  # Database client
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── ai_service.py       # Gemini: explanations, recipes, chat
│   │   │   ├── barcode_service.py  # OpenFoodFacts barcode lookup
│   │   │   ├── ocr_service.py      # Gemini Vision OCR extraction
│   │   │   ├── parser.py           # Gemini: structured text → JSON
│   │   │   └── scoring.py          # ⭐ Deterministic scoring engine
│   │   └── main.py                 # FastAPI app entry point
│   ├── db/
│   │   └── schema.sql              # Supabase database schema
│   ├── .env                        # Environment variables
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx                # Landing page
│   │   ├── scan/page.tsx           # Scan flow (upload → OCR → correct → results → chat)
│   │   ├── history/page.tsx        # Scan history
│   │   ├── layout.tsx              # Root layout
│   │   └── globals.css             # Global styles
│   ├── package.json
│   └── tsconfig.json
│
├── Gemini.md                       # Project specification & guidelines
└── README.md                       # You are here
```

---

## App Flow

```
📱 Open App
    │
    ├──→ 📷 Upload ingredient label photo
    │         │
    │         ▼
    │    🔤 Gemini Vision extracts text (OCR)
    │         │
    │         ▼
    │    ✏️ User reviews & corrects OCR text
    │         │
    │         ▼
    │    ⚙️ Rule-based engine calculates score
    │         │
    │         ▼
    │    📊 Results: Grade + Score + Breakdown
    │    💬 AI Explanation (neutral & educational)
    │    🍲 Homemade Alternative (regional Indian)
    │    🗨️ Chat: "Ask EcoSaur" about ingredients
    │
    └──→ 🏷️ Enter Barcode → OpenFoodFacts lookup → same flow
```

---

## Roadmap

### ✅ Phase 1 — MVP (Current)
- [x] Image upload & Gemini Vision OCR
- [x] Editable OCR correction layer
- [x] Deterministic rule-based scoring engine
- [x] Transparent score breakdown
- [x] AI-powered explanations
- [x] Homemade alternative suggestions
- [x] Barcode scanner (OpenFoodFacts)
- [x] Conversational chat UX
- [x] Scan history (localStorage)

### 🔲 Phase 2 — Enhanced Experience
- [ ] User authentication (Supabase Auth)
- [ ] Cloud-persisted scan history
- [ ] User health profiles (Weight Loss, Gym, Diabetic, Child-Friendly)
- [ ] Improved UI/UX polish & animations
- [ ] PWA support for mobile

### 🔲 Phase 3 — Advanced Features
- [ ] Product comparison engine
- [ ] Community recipe submissions
- [ ] Personalized scoring adjustments by health mode
- [ ] Gamification (streaks, badges, weekly insights)
- [ ] Ingredient knowledge base expansion

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
  <strong>🦕 EcoSaur — Guide users, don't scare them.</strong>
</p>
