# Local Setup Instructions


This guide will help you set up and run the Hindu Texts Q&A backend chatbot on your local machine.

## Prerequisites

- Python 3.8 or higher (Python 3.11 recommended)
- pip (Python package manager)

## Step 1: Clone or Download the Project

Download all the files from this Replit project to your local machine, including:
- All Python files
- The `attached_assets/` folder with your data files
- The `services/`, `routes/`, and `utils/` folders
- The `storage/` folder with the FAISS index

## Step 2: Install Dependencies

You have two options:

### Option A: Using pip with pyproject.toml (Recommended)
```bash
pip install -e .
```

### Option B: Using pip with individual packages
```bash
pip install email-validator faiss-cpu flask flask-sqlalchemy gunicorn mistralai pandas psycopg2-binary python-dotenv qdrant-client requests werkzeug
```

## Step 3: Set Up Environment Variables

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```
   OPENROUTER_API_KEY=your_actual_api_key_here
   ```

   To get an OpenRouter API key:
   - Visit: https://openrouter.ai/
   - Sign up and generate an API key
   - Paste it into your `.env` file
  
   - or use $Env:OPENROUTER_API_KEY="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"
   - echo $Env:OPENROUTER_API_KEY

3. (Optional) You can add a SESSION_SECRET in the `.env` file:
   ```
   SESSION_SECRET=your-random-secret-key
   ```

**Note:** The application now automatically loads environment variables from the `.env` file using python-dotenv. You don't need to manually export variables!

## Step 4: Verify Setup

Run the setup verification script:
```bash
python setup_local.py
```

This will check:
- Python version
- Installed dependencies
- Data files
- API configuration

## Running the Application

### Option 1: Command-Line Chatbot (Recommended)

Run the interactive chatbot:
```bash
python backend_chatbot.py --interactive
```

Or ask a single question:
```bash
python backend_chatbot.py -q "What is dharma?"
```

Get database stats:
```bash
python backend_chatbot.py --stats
```

View all options:
```bash
python backend_chatbot.py --help
```

### Option 2: Web API Server

Start the Flask API server:
```bash
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

Or using Flask directly:
```bash
python app.py
```

The API will be available at `http://localhost:5000`

#### API Endpoints

- **POST** `/api/search` - Search and answer questions
  ```bash
  curl -X POST http://localhost:5000/api/search \
    -H "Content-Type: application/json" \
    -d '{"question":"What is dharma?"}'
  ```

- **GET** `/api/verse/<chapter>/<verse>` - Get specific verse
  ```bash
  curl http://localhost:5000/api/verse/1/1
  ```

- **GET** `/api/stats` - Get database statistics
  ```bash
  curl http://localhost:5000/api/stats
  ```

- **POST** `/api/initialize` - Initialize/reload database
  ```bash
  curl -X POST http://localhost:5000/api/initialize \
    -H "Content-Type: application/json" \
    -d '{"force_reload":false}'
  ```

## Database

The system uses FAISS vector store by default with 45,784 indexed documents from:
- Bhagavad Gita
- Ramayana
- Mahabharata

The FAISS index is stored in `storage/` and `vector_index.faiss` files.

## Troubleshooting

### "Module not found" errors
Make sure all dependencies are installed:
```bash
pip install -e .
```

### API key issues
- Verify your `.env` file exists and contains valid API keys
- The application automatically loads the `.env` file
- Make sure `python-dotenv` is installed (it's included in the dependencies)

### Data files missing
- Ensure the `attached_assets/` folder is in your project directory
- Run `python setup_local.py` to verify data files

### Port already in use
If port 5000 is already in use, change it in `app.py` or use a different port:
```bash
gunicorn --bind 0.0.0.0:8000 main:app
```

## Features

- **Semantic search** across 45,784 Hindu text documents
- **AI-powered answers** with proper citations
- **Command-line interface** for easy interaction
- **RESTful API** for programmatic access
- **Verse lookup** by chapter and verse number
- **Multiple text sources** (Bhagavad Gita, Ramayana, Mahabharata)

## Notes

- The system works without API keys but won't generate AI answers (search only)
- FAISS provides fast local vector search without external databases
- All data is processed locally on your machine
