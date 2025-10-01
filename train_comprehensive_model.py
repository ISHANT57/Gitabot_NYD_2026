#!/usr/bin/env python3
"""
Comprehensive training script for Hindu texts Q&A system
Processes all available datasets including extensive Ramayana data
Target: 90-95% accuracy
"""

import logging
import sys
from services.rag_service import RAGService

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Comprehensive Hindu Texts Training ===")
    logger.info("Target: 90-95% accuracy with all datasets")
    
    try:
        # Initialize RAG service
        rag_service = RAGService()
        
        # Force reload to include all new Ramayana datasets
        logger.info("Initializing database with comprehensive datasets...")
        rag_service.initialize_database(force_reload=True)
        
        # Get final statistics
        stats = rag_service.get_database_stats()
        logger.info(f"Training completed successfully!")
        logger.info(f"Database statistics: {stats}")
        
        # Run some test queries to verify accuracy
        test_queries = [
            "What is dharma according to Krishna in the Bhagavad Gita?",
            "What does the Yoga Sutras say about meditation?",
            "Tell me about Hanuman in the Ramayana",
            "What happened when Rama met Sita for the first time?",
            "What are the main teachings of Patanjali?",
            "Describe Ravana's character in the Ramayana"
        ]
        
        logger.info("=== Testing System Accuracy ===")
        for i, query in enumerate(test_queries, 1):
            logger.info(f"Test {i}/6: {query}")
            result = rag_service.search_and_answer(query)
            logger.info(f"Confidence: {result.get('confidence', 0):.3f}")
            logger.info(f"Sources used: {result.get('context_used', 0)}")
            logger.info(f"Answer preview: {result.get('answer', '')[:100]}...")
            logger.info("---")
        
        logger.info("=== Training Complete ===")
        logger.info("Your Hindu texts Q&A system is now ready with comprehensive Ramayana data!")
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()