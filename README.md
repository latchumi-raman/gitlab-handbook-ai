# GitLab Handbook AI

An AI-powered chatbot for GitLab's Handbook and Direction pages, built with
React, FastAPI, Gemini 1.5 Flash, and Supabase pgvector.

## Live URLs
- **Frontend:** https://gitlab-handbook-ai.vercel.app
- **Backend API:** https://gitlab-handbook-ai-backend.onrender.com
- **API Docs:** https://gitlab-handbook-ai-backend.onrender.com/docs

## Tech Stack
| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.11, LangChain |
| AI | Gemini 1.5 Flash, text-embedding-004 |
| Database | Supabase (PostgreSQL + pgvector) |
| Hosting | Vercel (frontend), Render (backend) |
| CI/CD | GitHub Actions |

## Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/gitlab-handbook-ai.git
cd gitlab-handbook-ai
```

### 2. Backend setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your API keys (see below)
```

### 3. Frontend setup
```bash
cd frontend
npm install
cp .env.example .env.local
# Set VITE_API_BASE_URL=http://localhost:8000
```

### 4. Required API keys
| Key | Where to get it |
|---|---|
| `GEMINI_API_KEY` | https://aistudio.google.com → Get API Key |
| `SUPABASE_URL` | Supabase dashboard → Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase dashboard → Settings → API |

### 5. Run the data ingestion (once)
```bash
cd backend
python -m scripts.ingest --test-run    # quick test (15 pages)
python -m scripts.ingest               # full ingest
```

### 6. Run locally
```bash
# Terminal 1 — Backend
cd backend && python run.py

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Open http://localhost:5173

### 7. Run tests
```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

## Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for full deployment instructions.

## Architecture
- **RAG Pipeline:** Scrape → Chunk → Embed → Store in pgvector → Retrieve → Generate
- **Streaming:** FastAPI SSE → React EventStream reader
- **Guardrails:** Keyword + pattern classifier blocks off-topic queries
- **Analytics:** Every query logged to Supabase for the admin dashboard at `/admin`
