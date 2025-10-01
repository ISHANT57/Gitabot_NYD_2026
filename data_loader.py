#!/usr/bin/env python3
"""
Data loader script to initialize the vector database with Hindu texts.
Run this script to process and load all documents into the vector store.
"""

import logging
import sys
from services.rag_service import RAGService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main function to load data into the vector database"""
    try:
        logger.info("Starting data loading process...")
        
        # Initialize RAG service
        rag_service = RAGService()
        
        # Check if we should force reload
        force_reload = len(sys.argv) > 1 and sys.argv[1] == '--force'
        
        if force_reload:
            logger.info("Force reload requested")
        
        # Initialize database
        rag_service.initialize_database(force_reload=force_reload)
        
        # Get and display statistics
        stats = rag_service.get_database_stats()
        logger.info(f"Database initialization completed!")
        logger.info(f"Total documents: {stats.get('total_documents', 0)}")
        logger.info(f"Indexed documents: {stats.get('indexed_documents', 0)}")
        logger.info(f"Status: {stats.get('status', 'unknown')}")
        
        # Test search functionality
        logger.info("Testing search functionality...")
        test_result = rag_service.search_and_answer("What is dharma?")
        
        if test_result.get('answer'):
            logger.info("Search test successful!")
            logger.info(f"Test answer preview: {test_result['answer'][:100]}...")
            logger.info(f"Sources found: {len(test_result.get('sources', []))}")
        else:
            logger.warning("Search test returned no answer")
        
        logger.info("Data loading process completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
