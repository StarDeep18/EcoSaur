# EcoSaur Project Analysis

This analysis outlines the current architecture of the EcoSaur application, identifies security vulnerabilities and architectural gaps, and proposes a comprehensive production upgrade plan.

---

## 1. Current Architecture

Currently, the workspace consists of:
*   **Mobile App (`/mobile`)**: A React Native Expo application structured with a mix of Expo Router screens (`mobile/app`) and inline styling/logic. There is a single routing structure under `mobile/app` (`index.tsx`, `scan.tsx`, `correction.tsx`, `results.tsx`). The app uses NativeWind for styling.
*   **Backend Server (`/backend`)**: A FastAPI Python application (`backend/app`) that uses a SQLite database (`ecosaur_sqlite.db`) for storing local data, including user preference configurations, crowdsourced barcode data, and scan history.
*   **Frontend Client (`/frontend`)**: A Next.js web application configured to communicate with the FastAPI backend.
*   **Database**: A local SQLite file (`ecosaur_sqlite.db`) with schemas for users, product categories, products, ingredients, alternatives, scans, corrections, and moderation items.

---

## 2. Problems & Security Issues Found

*   **Hardcoded API Keys**:
    *   The Gemini API Key (`placeholder_gemini_key`) is hardcoded directly inside `backend/app/core/config.py`.
    *   The backend's `.env` contains the same hardcoded key.
*   **Insecure API Hostnames in Mobile**:
    *   The base URL in `mobile/services/api.ts` is hardcoded to a local private IP address (`http://10.136.73.160:8000/api/v1`), which will break across different networks and when deployed.
*   **Lack of Authentication**:
    *   There is no user authentication mechanism. The API uses a hardcoded `'default'` string as the user ID for most operations.
    *   There are no Login, Registration, or Profile screens in the mobile app.
*   **Local SQLite Database for Production**:
    *   A production mobile app needs a centralized cloud database. Using a local SQLite file in the backend folder does not allow horizontal scaling or persistent state across distributed servers.
    *   No Row Level Security (RLS) is active.
*   **Deterministic Scoring Inconsistencies**:
    *   The backend score calculator in `backend/app/services/scoring.py` uses NOVA groups and sugar loads but doesn't align exactly with the strict deterministic scoring requested (e.g., base 100, sugar -15, trans fat -30, high protein +10, fiber +10, and letter grades S-F).
*   **Lack of Rate Limiting / API Protection**:
    *   The FastAPI backend has no rate limiting or scan limiting mechanism. Anyone can make infinite requests to OCR and Gemini models, exposing the platform to massive token usage bills.
*   **Code Organization & Cleanliness**:
    *   The mobile app files contain some TS errors and inline styles that should be properly modularized. The directory lacks separate folders like `components/`, `screens/`, `navigation/`, `hooks/`, `constants/`, and `types/` under `src`.

---

## 3. Target Final Architecture

```
Mobile App (Expo React Native)
            │
            ▼ (HTTPS API + Auth Token)
      Backend Server (FastAPI)
      ┌─────┴──────┬────────────────┐
      ▼            ▼                ▼
   Supabase      Gemini       Scoring Engine
(Auth & DB)  (AI Generation)  (Deterministic)
```

The mobile app will interact strictly with the Backend Server, authenticating requests via Supabase Auth tokens. The backend acts as a secure proxy to the database, Gemini, and the scoring logic.

---

## 4. Phase-by-Phase Upgrade Plan

### Phase 1: Clean Existing Project (Mobile Structure)
*   Create a clean directory structure under `mobile/src/` containing: `components`, `screens`, `navigation`, `services`, `hooks`, `utils`, `constants`, `types`, and `assets`.
*   Move existing screens (`index.tsx`, `scan.tsx`, `results.tsx`, `correction.tsx`) to `mobile/src/screens` and reference them cleanly.
*   Resolve TypeScript compiling warnings and clean imports.
*   Ensure compatibility with Expo Go.

### Phase 2: Environment Security
*   Remove all hardcoded keys.
*   Create `backend/.env.example` and `mobile/.env.example`.
*   Configure backend `config.py` to read `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_ANON_KEY` from the environment.
*   Update `.gitignore` to ensure `.env`, `node_modules`, and build files are ignored.

### Phase 3: Backend Restructure
*   Move backend source files to `backend/src/`.
*   Organize code into:
    *   `src/routes/` (for analyze, history, auth routes)
    *   `src/services/` (for Gemini, scoring, OCR)
    *   `src/middleware/` (for auth verification, rate limiting)
    *   `src/config/` (for config settings)
    *   `src/main.py` (server entry point)
*   Secure routes behind auth middleware verifying Supabase JWTs.

### Phase 4: Gemini Security Refactor
*   Review frontend/mobile code to guarantee that no direct Gemini calls exist.
*   All AI interactions (OCR, score explanation, alternative recipe generation, conversational chat) must go through the backend API.

### Phase 5: Supabase Auth Implementation
*   Integrate Supabase Client (`@supabase/supabase-js`) in the mobile app.
*   Build:
    *   `LoginScreen`
    *   `RegisterScreen`
    *   `ProfileScreen`
*   Configure session persistence and update the navigation layout so unauthenticated users are forced to Login/Register.

### Phase 6: Database Integration (Supabase)
*   Create table schemas in Supabase matching:
    *   `profiles`: `id` (references auth.users), `email`, `created_at`
    *   `scan_history`: `id`, `user_id`, `ingredients`, `score`, `grade`, `explanation`, `alternative_recipe`, `created_at`
    *   `api_usage`: `id`, `user_id`, `scan_count`, `date`
*   Enable Row Level Security (RLS) policies on these tables to guarantee users only access their own data.
*   Update backend repositories/CRUD services to interface with Supabase instead of SQLite.

### Phase 7: Scoring Engine Refactor
*   Rebuild `scoring.service` in the backend to calculate scores deterministically:
    *   Base score: 100
    *   Added sugar: -15
    *   Trans fat: -30 (derived from hydrogenated/partially hydrogenated oils or nutrition labels)
    *   High protein: +10
    *   Fiber: +10
    *   Ensure scores stay in the 0-100 range.
    *   Assign grades: S (90-100), A (80-89), B (70-79), C (60-69), D (40-59), F (<40).
    *   Return detailed scorecard metadata containing positives and negatives.

### Phase 8: Gemini AI Layer Refactoring
*   Restrict data passed to Gemini to: ingredients, score, grade, reasons.
*   Write system instructions ensuring Gemini:
    *   Never attacks food brands.
    *   Never creates fear or alarmism (no "poison", "dangerous", etc.).
    *   Never gives medical advice.
    *   Focuses purely on neutral educational value and suggests simple regional alternatives.

### Phase 9: Mobile Scan History Screen
*   Add a `HistoryScreen` in the mobile app.
*   Display previous scans (food name, grade, score, date).
*   Add clickable rows to re-render the corresponding guide card in `ResultsScreen`.

### Phase 10: API Usage Limiting
*   Create a rate-limiting middleware in the backend.
*   For each scan request, query `api_usage` for the current user and date.
*   Limit free users to 10 scans/day. Return an HTTP 429 status with a friendly explanation once exceeded.

### Phase 11: UI/UX Polishing
*   Add clean loading indicators and skeleton views for scanning/analysis.
*   Design custom result card widgets and visual grade badge states (e.g., color-coded labels).
*   Ensure empty/error states are graceful.

### Phase 12: Testing
*   Write Python unit tests for the deterministic scoring engine.
*   Write mock tests for routes and rate-limiting.
*   Ensure all tests pass and standard builds succeed.

### Phase 13: Deployment & Licensing
*   Ensure backend is compatible with platforms like Render/Railway.
*   Ensure mobile project is ready for EAS build configurations.
*   Create a detailed `README.md` and append an `MIT License`.
