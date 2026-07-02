# Hindu Texts Q&A System

## Overview

This is a Retrieval-Augmented Generation (RAG) system that provides AI-powered semantic search and question-answering capabilities for Hindu religious texts. The system processes and indexes sacred texts including the Bhagavad Gita, Ramayana, and Mahabharata, allowing users to ask questions in natural language and receive contextually relevant answers with proper citations from the original sources.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Web Framework Architecture
- **Flask-based web application** with Blueprint organization for modular route management
- **RESTful API endpoints** for search functionality and verse lookup

### RAG (Retrieval-Augmented Generation) Pipeline
- **Document Processing Layer**: Handles multiple file formats (CSV, TXT, JSON) containing religious texts
- **Text Chunking Strategy**: Splits documents into 400-token chunks with 100-token overlap for optimal retrieval
- **Embedding Generation**: Uses Mistral AI's embedding model for semantic understanding
- **Vector Storage**: Qdrant vector database for efficient similarity search
- **Answer Generation**: Combines retrieved context with LLM prompting for accurate responses

### Data Processing Architecture
- **Multi-format ingestion**: Processes CSV files with Q&A pairs, plain text editions, and JSON verse collections
- **Metadata preservation**: Maintains chapter, verse, and source information for proper citation
- **Content normalization**: Handles Sanskrit text, translations, explanations, and related questions
- **Chunking with overlap**: Ensures context preservation across document boundaries

### Service Layer Design
- **RAGService**: Central orchestrator managing the complete question-answering workflow
- **DocumentProcessor**: Handles file parsing and text preparation for multiple formats
- **VectorStore**: Abstracts Qdrant operations for document storage and retrieval
- **APIClient**: Manages external API calls with fallback mechanisms between providers

### Configuration Management
- **Environment-based configuration** using the Config class for API keys and settings
- **Flexible model selection** supporting both Mistral AI and OpenRouter as LLM providers
- **Tunable parameters** for chunk size, similarity thresholds, and retrieval settings

## External Dependencies

### AI/ML Services
- **Mistral AI**: Primary provider for text embeddings and language model inference
- **OpenRouter**: Fallback service for embeddings and chat completions when Mistral is unavailable
- Both services provide hosted model access without requiring local model downloads

### Vector Database
- **Qdrant**: Vector database for storing document embeddings and performing similarity search
- Supports both cloud-hosted and self-hosted deployment options
- Configured for cosine similarity with 1024-dimensional embeddings

### Python Libraries
- **Flask**: Web framework with Blueprint support and template rendering
- **Pandas**: Data processing for CSV files containing verses and Q&A pairs
- **Requests**: HTTP client for external API communication
- **Qdrant Client**: Python SDK for vector database operations

### Development and Deployment
- **Environment Variables**: Secure management of API keys and configuration
- **Logging**: Comprehensive logging throughout the application stack
- **Error Handling**: Graceful fallbacks and user-friendly error messages
- **WSGI Deployment**: Production-ready setup with ProxyFix middleware

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Required | Purpose |
|----------|----------|---------|
| `MISTRAL_API_KEY` | Yes | Real embeddings (`mistral-embed`). Used both when building the index **and** to embed every query at runtime. |
| `GEMINI_API_KEY` | Yes | Primary answer generation. |
| `GEMINI_MODEL` | No | Answer model. Defaults to `gemini-2.5-flash`. |
| `OPENROUTER_API_KEY` | No | Optional fallback answer generator (Mixtral 8x7B). |
| `HF_REPO_ID` | Deploy | HuggingFace dataset repo holding the prebuilt index. |
| `HF_TOKEN` | If private | HuggingFace token; needed only if the index repo is private. |
| `PORT` | No | Port for the dev server (`main.py`). Defaults to `5000`. |
| `FLASK_DEBUG` | No | `true` to enable Flask debug mode locally. Defaults to off. |
| `LOG_LEVEL` | No | Log verbosity. Defaults to `INFO` (use `DEBUG` locally; avoid in prod — DEBUG logs the API key in request URLs). |
| `SESSION_SECRET` | No | Flask session secret. |

## Local Development

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

# Build the FAISS index from attached_assets/ (needs MISTRAL_API_KEY):
python -c "from services.rag_service import RAGService; RAGService().initialize_database(force_reload=True)"

python main.py   # serves on http://localhost:5000  (override with PORT)
```

## The Vector Index

The index (`vector_index.faiss` + `metadata.json`, ~230 MB) is **not** committed to git.
It is stored on a HuggingFace dataset repo and pulled at deploy time.

- **Publish** a freshly built index: `python upload_index.py` (needs `HF_TOKEN` with write access).
- **Download** happens automatically on deploy via `download_index.py`.

> Rebuild + re-upload the index whenever the corpus or embedding model changes,
> or production will serve a stale index.

## Deploying on Render

The repo includes `render.yaml` (Blueprint). Steps:

1. **New → Web Service** and connect this GitHub repo; Render auto-detects `render.yaml`.
2. **Instance type: Standard (2 GB RAM) or larger.** The index loads fully into memory
   (~1.3 GB); the 512 MB Free/Starter tiers will OOM on boot.
3. Set the secret env vars (marked `sync: false`) in the dashboard:
   `MISTRAL_API_KEY`, `GEMINI_API_KEY` (and `GEMINI_MODEL=gemini-2.5-flash`).
   Set `HF_TOKEN` only if the index repo is private.
4. Deploy. Boot runs `download_index.py` (pulls the index from HuggingFace) then
   gunicorn. The `/api/stats` health check turns green once the index is loaded.

Notes:
- Every query embeds via the Mistral API, so `MISTRAL_API_KEY` must be set in production.
- Gemini free-tier quotas apply; heavy traffic may hit `429`. Enable billing on the
  Google project for a reliable public deployment.
