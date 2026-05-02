# Hindu Texts Q&A Chatbot

## Overview
A Flask-based Python backend for a Hindu Texts Q&A chatbot using RAG (Retrieval-Augmented Generation). It provides semantic search across Hindu religious texts (Bhagavad Gita, Ramayana, Mahabharata) and AI-powered answers via OpenRouter's Mixtral 8x7B model.

## Architecture
- **Backend**: Flask web API (Python 3.11)
- **Vector Search**: FAISS (local) with optional Qdrant fallback
- **Embeddings**: Hash-based (local, no API) for indexing; OpenRouter API for queries
- **LLM**: Mixtral 8x7B Instruct via OpenRouter API
- **Data**: 45,784+ indexed documents from Hindu texts in `attached_assets/`

## Project Structure
- `app.py` — Flask app factory, registers blueprints
- `main.py` — Entry point for gunicorn
- `config.py` — Configuration (API keys, model names, data file paths)
- `routes/main.py` — API route handlers
- `services/rag_service.py` — RAG pipeline (search + answer generation)
- `services/faiss_vector_store.py` — FAISS vector store (primary)
- `services/vector_store.py` — Qdrant vector store (optional, auto-falls back to FAISS)
- `services/api_client.py` — OpenRouter/Mistral API client
- `services/document_processor.py` — CSV/JSON/TXT document processor
- `utils/text_utils.py` — Text chunking and normalization
- `attached_assets/` — Data files (CSV, JSON, TXT)
- `storage/` — FAISS index persistence

## API Endpoints
- `POST /api/search` — Search and answer a question
- `GET /api/verse/<chapter>/<verse>` — Get a specific verse
- `GET /api/stats` — Get database statistics
- `POST /api/initialize` — Initialize/reload the vector database

## Environment Variables
- `OPENROUTER_API_KEY` — Required for AI answer generation (get from openrouter.ai)
- `MISTRAL_API_KEY` — Optional fallback embedding API
- `QDRANT_URL` — Optional Qdrant URL (defaults to localhost:6333, falls back to FAISS)
- `SESSION_SECRET` — Flask session secret key

## Running
The app runs via gunicorn on port 5000:
```
gunicorn --bind=0.0.0.0:5000 --reuse-port --reload main:app
```

## Notes
- FAISS vector store is used by default (Qdrant not available in Replit)
- The FAISS index is empty on fresh clone — use `POST /api/initialize` to load data
- System works without API keys but won't generate AI answers (search only)
- Deployment configured as autoscale on Replit
