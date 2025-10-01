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
