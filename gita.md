# Hindu Texts Q&A Chatbot - Complete Setup Guide

Welcome! This guide will help you run the Hindu Texts Q&A Chatbot on your local computer. This application lets you search and ask questions about Hindu texts including the Bhagavad Gita, Ramayana, and Mahabharata.

## What You'll Get

- ✅ Search across 45,784 documents from Hindu texts
- ✅ AI-powered answers to your questions
- ✅ Command-line chatbot interface
- ✅ Web API for programmatic access
- ✅ Verse lookup by chapter and verse number
- ✅ Everything runs locally on your computer

---

## Prerequisites

Before you begin, make sure you have:

1. **Python 3.8 or higher** (Python 3.11 recommended)
   - Download from: https://www.python.org/downloads/
   
2. **pip** (Python package manager - usually comes with Python)

3. **A text editor** (Notepad, VS Code, Sublime Text, etc.)

---

## Step-by-Step Installation

### Step 1: Download the Project

Download all files from this project to a folder on your computer. Make sure you have:

- ✅ All Python files (`.py` files)
- ✅ The `attached_assets/` folder (contains 45,784+ Hindu text documents)
- ✅ The `services/`, `routes/`, and `utils/` folders
- ✅ The `storage/` folder (contains the pre-built search index)
- ✅ The `.env.example` file
- ✅ The `pyproject.toml` file

### Step 2: Check Python Installation

Open your terminal/command prompt and check if Python is installed:

**On Windows:**
```bash
python --version
```

**On Mac/Linux:**
```bash
python3 --version
```

You should see something like `Python 3.11.x`. If not, install Python from https://www.python.org/downloads/

### Step 3: Navigate to Project Folder

Open terminal/command prompt and go to your project folder:

**Windows:**
```bash
cd C:\path\to\your\project
```

**Mac/Linux:**
```bash
cd /path/to/your/project
```

### Step 4: Install Required Packages

Run this command to install all dependencies:

```bash
pip install -e .
```

**If that doesn't work, try:**

```bash
pip install email-validator faiss-cpu flask flask-sqlalchemy gunicorn mistralai pandas psycopg2-binary python-dotenv qdrant-client requests werkzeug
```

**Or on Mac/Linux:**
```bash
pip3 install -e .
```

This may take a few minutes. Wait for all packages to install.

### Step 5: Set Up Your API Key

The chatbot needs an API key to generate AI-powered answers.

#### 5.1: Copy the Environment File

**On Windows:**
```bash
copy .env.example .env
```

**On Mac/Linux:**
```bash
cp .env.example .env
```

#### 5.2: Get Your Free API Key

1. Visit: **https://openrouter.ai/**
2. Sign up for a free account
3. Go to "API Keys" section
4. Create a new API key and copy it

#### 5.3: Add Your API Key

1. Open the `.env` file with any text editor (Notepad, TextEdit, etc.)
2. Find this line:
   ```
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   ```
3. Replace `your_openrouter_api_key_here` with your actual API key:
   ```
   OPENROUTER_API_KEY=sk-or-v1-abc123xyz456...
   ```
4. Save and close the file

**Note:** Without an API key, the app still works for searching texts, but won't generate AI answers.

### Step 6: Verify Everything is Set Up

Run the verification script:

**On Windows:**
```bash
python setup_local.py
```

**On Mac/Linux:**
```bash
python3 setup_local.py
```

This checks if everything is installed correctly.

---

## Running the Application

You have two ways to use the application:

### Option A: Command-Line Chatbot (Easiest & Recommended)

This is the simplest way to use the chatbot. It works like ChatGPT in your terminal.

#### Start Interactive Chat Mode:

**On Windows:**
```bash
python backend_chatbot.py --interactive
```

**On Mac/Linux:**
```bash
python3 backend_chatbot.py --interactive
```

You'll see a prompt where you can ask questions:
```
🕉️  Hindu Texts Q&A Chatbot
📚 Ask questions about Bhagavad Gita, Ramayana, Mahabharata
💬 Type your question (or 'quit' to exit):
> What is dharma?
```

#### Ask a Single Question:

**On Windows:**
```bash
python backend_chatbot.py -q "What is dharma?"
```

**On Mac/Linux:**
```bash
python3 backend_chatbot.py -q "What is dharma?"
```

#### Get Database Statistics:

**On Windows:**
```bash
python backend_chatbot.py --stats
```

**On Mac/Linux:**
```bash
python3 backend_chatbot.py --stats
```

#### View All Available Options:

**On Windows:**
```bash
python backend_chatbot.py --help
```

**On Mac/Linux:**
```bash
python3 backend_chatbot.py --help
```

---

### Option B: Web API Server

This starts a web server so you can access the chatbot through your browser or build your own interface.

#### Start the Server:

**On Windows:**
```bash
python app.py
```

**On Mac/Linux:**
```bash
python3 app.py
```

You'll see:
```
 * Running on http://0.0.0.0:5000
```

The server is now running! Keep this terminal window open.

#### Access the API:

Open your browser and go to: **http://localhost:5000**

Or use the API endpoints:

**1. Search and Ask Questions:**
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"question":"What is dharma?"}'
```

**2. Get a Specific Verse:**
```bash
curl http://localhost:5000/api/verse/1/1
```

**3. Get Database Statistics:**
```bash
curl http://localhost:5000/api/stats
```

**4. Initialize/Reload Database:**
```bash
curl -X POST http://localhost:5000/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload":false}'
```

---

## Example Questions You Can Ask

- "What is dharma?"
- "What does Krishna say about karma?"
- "Tell me about Arjuna's dilemma"
- "What is the importance of devotion?"
- "Explain the concept of moksha"
- "What are the qualities of a wise person?"
- "How should one perform their duty?"

---

## Troubleshooting

### Problem: "Python is not recognized" or "command not found"

**Solution:** Python is not installed or not in your PATH.
- Install Python from https://www.python.org/downloads/
- On Windows, make sure to check "Add Python to PATH" during installation
- Restart your terminal after installation

### Problem: "Module not found" errors

**Solution:** Dependencies are not installed.
```bash
pip install -e .
```

If that doesn't work:
```bash
pip install email-validator faiss-cpu flask flask-sqlalchemy gunicorn mistralai pandas psycopg2-binary python-dotenv qdrant-client requests werkzeug
```

### Problem: "Permission denied" errors

**Solution:** Use `pip` with `--user` flag:
```bash
pip install --user -e .
```

### Problem: API key not working

**Solution:**
- Check that your `.env` file exists in the same folder as `app.py`
- Make sure there are no extra spaces in your API key
- Verify your API key is valid at https://openrouter.ai/
- The `.env` file should look like:
  ```
  OPENROUTER_API_KEY=sk-or-v1-abc123...
  ```

### Problem: "Port 5000 already in use"

**Solution:** Another application is using port 5000.
- Close other applications that might be using port 5000
- Or edit `app.py` and change `port=5000` to `port=8000` (or any other port)

### Problem: Missing data files

**Solution:** Make sure you downloaded the complete project.
- The `attached_assets/` folder must contain CSV and JSON files
- The `storage/` folder should exist
- Run `python setup_local.py` to verify all files

### Problem: Slow responses

**Solution:** This is normal for the first run.
- The system loads 45,784 documents on first run
- Subsequent queries will be faster
- Make sure you have at least 2GB of free RAM

---

## Important Notes

✅ **Privacy:** Everything runs locally on your computer. Your questions are only sent to OpenRouter API for answer generation.

✅ **Offline Search:** The search functionality works offline. Only AI answer generation requires internet.

✅ **No API Key?** The app still works without an API key! You can search texts and find relevant passages, but won't get AI-generated answers.

✅ **Data Included:** All 45,784 documents from Bhagavad Gita, Ramayana, and Mahabharata are pre-indexed and ready to use.

✅ **Free to Use:** This is open-source software. Use it however you like!

---

## System Requirements

- **Operating System:** Windows 10+, macOS 10.14+, or Linux
- **Python:** 3.8 or higher (3.11 recommended)
- **RAM:** At least 2GB free
- **Disk Space:** At least 500MB free
- **Internet:** Required only for API key setup and AI answer generation

---

## Need Help?

If you encounter any issues not covered in this guide:

1. Check that all files are downloaded completely
2. Verify Python version: `python --version`
3. Try reinstalling dependencies: `pip install -e .`
4. Make sure your `.env` file is set up correctly
5. Run the verification script: `python setup_local.py`

---

## Features Overview

### What This Application Does:

1. **Semantic Search:** Find relevant passages across all Hindu texts using advanced vector search
2. **AI Answers:** Get comprehensive answers with proper citations from the original texts
3. **Verse Lookup:** Retrieve specific verses by chapter and verse number
4. **Multiple Interfaces:** Use command-line chatbot or web API
5. **Source Attribution:** Every answer includes the source text and verse reference

### Technology Used:

- **Flask:** Web framework for API server
- **FAISS:** Fast vector search for finding relevant passages
- **OpenRouter:** AI model access for generating answers
- **Python:** Core programming language

---

## Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] All project files downloaded
- [ ] Dependencies installed (`pip install -e .`)
- [ ] `.env` file created from `.env.example`
- [ ] OpenRouter API key added to `.env` file
- [ ] Verification script run successfully
- [ ] Application started (chatbot or web server)

Once all checkboxes are complete, you're ready to use the chatbot!

---

## License & Credits

This application searches and analyzes classical Hindu texts for educational purposes. All texts are in the public domain.

**Texts Included:**
- Bhagavad Gita
- Valmiki Ramayana
- Mahabharata

Enjoy exploring the wisdom of Hindu texts! 🕉️
