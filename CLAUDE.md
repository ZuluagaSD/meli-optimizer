# MeliOptimizer — AI-powered Mercado Libre Listing Optimization SaaS

## Quick Start (Local Dev)

```bash
# Terminal 1 — Backend (FastAPI + SQLite)
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Frontend (Next.js)
cd frontend && npm run dev

# Seed demo data (run once)
curl -X POST http://localhost:8000/api/seed

# Demo login: demo@melioptimizer.com / demo1234
```

## Architecture

- **Backend**: Python FastAPI (`backend/app/`) — SQLite for dev, PostgreSQL for prod
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS 4 (`frontend/src/`)
- **AI**: Claude API via `anthropic` SDK for title optimization & attribute suggestions
- **Infra**: Docker Compose (postgres + redis) for production; SQLite + in-memory cache for local dev

## Project Structure

```
backend/app/
  main.py              # FastAPI app entry, mounts all routers at /api
  config.py            # Settings from env vars (pydantic-settings)
  db/database.py       # Async SQLAlchemy engine, session, init_db()
  models/              # SQLAlchemy models: Tenant, User, MeliAccount, Listing, Optimization
  routers/             # API routes: auth, listings, optimize, dashboard, seed
  services/
    auth_service.py    # MeLi OAuth 2.0 + JWT platform auth + bcrypt passwords
    meli_client.py     # MeLi API wrapper with rate limiting (1500 req/min) + auto token refresh
    listing_sync.py    # Import listings via MeLi scroll pagination
    optimizer.py       # Claude API prompt builder (es-AR, pt-BR, es-MX templates)

frontend/src/
  app/                 # Next.js App Router pages (dashboard, listings, listings/[id], optimize, auth)
  components/          # Sidebar
  lib/api.ts           # Typed API client with JWT auth
  lib/utils.ts         # Currency formatting, health/completeness color helpers
  i18n/                # es.json, pt.json translation files
```

## Key Decisions

- IDs are `String(36)` UUIDs (SQLite-compatible, works with PostgreSQL too)
- JSON columns instead of JSONB/ARRAY for cross-DB compatibility
- In-memory dict cache in optimizer.py (swap to Redis for production)
- bcrypt directly (not passlib) due to passlib/bcrypt version incompatibility
- MeLi tokens encrypted with Fernet at rest (TOKEN_ENCRYPTION_KEY env var)

## Running Tests

```bash
cd backend && python -m pytest tests/ -v
```

9 unit tests covering: auth (password hashing, JWT, OAuth URLs), listing sync (attribute completeness, health detection), optimizer (language selection, attribute formatting).

## Environment Variables

See `.env.example`. Key ones:
- `ANTHROPIC_API_KEY` — required for AI title/attribute optimization
- `MELI_APP_ID` / `MELI_SECRET_KEY` — for real MeLi OAuth (demo works without)
- `TOKEN_ENCRYPTION_KEY` — Fernet key for encrypting MeLi tokens at rest
- `SECRET_KEY` — JWT signing key

## Multi-Market Support

- MLA (Argentina) — Spanish (es-AR), ARS currency
- MLB (Brasil) — Portuguese (pt-BR), BRL currency
- MLM (México) — Spanish (es-MX), MXN currency

Each market gets country-specific Claude prompt templates in `optimizer.py`.
