# Steam Price Tracker — Backend

FastAPI backend for [Games Price Dashboard](https://games-stats.vercel.app/) ([frontend repo](https://github.com/faisal-almugesib/steamPriceFrontend)). Searches Steam games, aggregates price history across stores, and predicts the next discount.

## Architecture

```
React frontend (Vercel)
        │
        ▼
FastAPI backend ──► Steam Store API        (search, game details)
        │      ──► IsThereAnyDeal API      (historical lows, price history)
        │      ──► Gemini 1.5 Flash        (discount prediction from price stats)
```

- **`main.py`** — API surface: `/search`, `/price-history/{game_id}`, `/predict-discount/{game_id}`, `/game-details/{game_id}`
- **`services/steam_api.py`** — async Steam Store search + app details (httpx)
- **`services/price_history.py`** — Steam App ID → ITAD lookup → store-low history, normalized for charting
- **`services/discount_predictor.py`** — computes price statistics (current/low/high/average, store coverage) and prompts Gemini for a structured discount prediction with confidence
- **`models/schemas.py`** — Pydantic response models
- **`scripts/`** — standalone API exploration scripts

## Run Locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# .env
# ITAD_API_KEY=...      (https://isthereanydeal.com/dev/app/)
# GEMINI_API_KEY=...    (https://aistudio.google.com/)

uvicorn main:app --reload   # Swagger UI at http://127.0.0.1:8000/docs
```

`/search` and `/game-details` work without any API keys; price history needs `ITAD_API_KEY`, prediction needs `GEMINI_API_KEY`.

## Fallback behavior (no keys required)

The API is fully usable without keys: if `ITAD_API_KEY` is missing or the ITAD call fails, `/price-history` returns **deterministic sample price data** (real game title still fetched from Steam); if `GEMINI_API_KEY` is missing or the Gemini call fails, `/predict-discount` returns a **statistical estimate** computed from the price history. Fallback responses carry `"fallback": true` and a `"note"` string, which the frontend renders as small grey text so sample data is never mistaken for live data.

## Deployment

The frontend is live on Vercel: **[games-stats.vercel.app](https://games-stats.vercel.app/)**.

The backend runs as a **Vercel serverless function** (free Hobby plan) — `vercel.json` is included, so importing this repo at [vercel.com/new](https://vercel.com/new) deploys it with no extra configuration. Point the frontend's `VITE_BACKEND_URL` environment variable at the resulting URL. API keys (`ITAD_API_KEY`, `GEMINI_API_KEY`) are optional — without them the API serves the sample-data fallback described above.

It also runs on any regular Python host: `uvicorn main:app --host 0.0.0.0 --port $PORT` (Procfile included).
