import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # API Configuration
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "default_mistral_key")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "default_openrouter_key")
    
    # Vector Database Configuration
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
    QDRANT_COLLECTION_NAME = "hindu_texts"
    
    # Text Processing Configuration
    CHUNK_SIZE = 400  # tokens
    CHUNK_OVERLAP = 100  # tokens (25% overlap)
    SIMILARITY_THRESHOLD = 0.65
    
    # Model Configuration
    EMBEDDING_MODEL = "mistral-embed"
    LLM_MODEL = "mistralai/mixtral-8x7b-instruct"
    
    # Data Files
    DATA_DIR = "attached_assets"
    
    @classmethod
    def get_data_files(cls):
        return {
            # High-quality Bhagavad Gita sources
            "bhagavad_gita_qa": "Bhagwad_Gita_Verses_English_Questions_1757068789961.csv",
            "processed_gita": "processed_bhagwat_gita_1757068789966.csv",
            
            # High-quality Ramayana sources
            "ramayana_verses_comprehensive": "valmiki-ramayana-verses_1757069097291.json",
            "ramayana_iyd_dataset": "iyd_dataset_final - Sheet1_1757074628351.json",
            
            # High-quality Mahabharata sources  
            "mahabharata_characters": "mahabharata_1757074722541.json",
            "ramayana_characters": "ramayana_1757074722540.json"
        }
