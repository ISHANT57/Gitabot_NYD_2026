import logging
import time
from typing import List, Dict, Any, Optional
from services.api_client import APIClient
from services.faiss_vector_store import FaissVectorStore
from utils.text_utils import TextNormalizer
from config import Config

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.config = Config()
        self.api_client = APIClient()

        self.vector_store = FaissVectorStore()
        logger.info("Using FAISS vector store")

        # DocumentProcessor (and its heavy pandas dependency) is only needed when
        # building the index, so it is imported lazily to keep the serving
        # process lightweight. See _get_doc_processor().
        self.doc_processor = None
        self.normalizer = TextNormalizer()

    def _get_doc_processor(self):
        """Lazily construct the DocumentProcessor (imports pandas) on first use."""
        if self.doc_processor is None:
            from services.document_processor import DocumentProcessor
            self.doc_processor = DocumentProcessor()
        return self.doc_processor
    
    def initialize_database(self, force_reload: bool = False):
        """Initialize the vector database with documents"""
        try:
            # Check if collection already has data
            info = self.vector_store.get_collection_info()
            if info.get("points_count", 0) > 0 and not force_reload:
                logger.info(f"Database already initialized with {info['points_count']} documents")
                return
            
            if force_reload:
                logger.info("Force reloading database...")
                self.vector_store.clear_collection()
            
            # Process all documents
            logger.info("Processing documents...")
            documents = self._get_doc_processor().process_all_files()
            
            if not documents:
                logger.warning("No documents found to process")
                return
            
            # Generate real embeddings for all documents (batched via the Mistral API).
            # Index and query must use the SAME embedding method or search is meaningless.
            logger.info(f"Generating embeddings for {len(documents)} documents (batched)...")
            texts = [doc["text"] for doc in documents]
            embeddings = self.api_client.get_embeddings(texts, use_api=True)
            for doc, embedding in zip(documents, embeddings):
                doc["embedding"] = embedding

            # Filter out documents without embeddings
            valid_documents = [doc for doc in documents if "embedding" in doc]
            logger.info(f"Generated embeddings for {len(valid_documents)} documents")
            
            # Add to vector store
            if valid_documents:
                self.vector_store.add_documents(valid_documents)
                logger.info("Database initialization completed successfully")
            else:
                logger.error("No valid documents with embeddings to add to database")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def search_and_answer(self, question: str, source_filter=None) -> Dict[str, Any]:
        """Search for relevant documents and generate an answer"""
        try:
            # Check if question is related to Hindu texts
            if not self._is_hindu_text_related(question):
                return {
                    "answer": "I can only answer questions about Hindu religious texts including the Bhagavad Gita, Ramayana, Mahabharata, and Yoga Sutras. Please ask questions related to these sacred texts, their teachings, characters, or philosophical concepts.",
                    "confidence": 0.0
                }
            
            # Normalize the question
            normalized_question = self.normalizer.normalize_query(question)
            
            # Generate embedding for the question
            question_embedding = self.api_client.get_embedding(normalized_question)
            
            # Search for relevant documents with expanded scope
            search_results = self.vector_store.search(
                query_embedding=question_embedding,
                limit=20,  # Get more results to improve chances of finding relevant content
                source_filter=source_filter
            )
            
            # Drop weak matches so the LLM is never fed irrelevant context
            search_results = [
                r for r in search_results
                if r.get("score", 0) >= self.config.SIMILARITY_THRESHOLD
            ]

            if not search_results:
                return {
                    "answer": "Based on the available texts, I cannot find relevant information to answer this question. Please try rephrasing your question or asking about specific verses or concepts from the Bhagavad Gita or Yoga Sutras.",
                    "confidence": 0.0
                }

            # Prepare context from search results
            context_parts = []
            
            for result in search_results[:5]:  # Use top 5 results
                # Format the context entry
                context_entry = self._format_context_entry(result)
                context_parts.append(context_entry)
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Generate answer
            answer = self.api_client.generate_answer(question, context)
            
            # Calculate average confidence score
            top_results = search_results[:5]
            avg_confidence = sum(r["score"] for r in top_results) / len(top_results)
            
            # Build source list for UI display
            sources = []
            for r in top_results:
                source_entry = {
                    "source": r.get("source", ""),
                    "chapter": r.get("chapter", ""),
                    "verse": r.get("verse", ""),
                    "text": r.get("text", "")[:300],
                    "translation": r.get("translation", "")[:300],
                    "score": round(r.get("score", 0), 3)
                }
                sources.append(source_entry)
            
            return {
                "answer": answer,
                "confidence": avg_confidence,
                "context_used": len(context_parts),
                "sources": sources
            }
            
        except Exception as e:
            logger.error(f"Error in search_and_answer: {e}")
            return {
                "answer": "I encountered an issue while searching for your answer. This might be due to a temporary service interruption. Please try rephrasing your question or try again in a moment.",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _format_context_entry(self, result: Dict[str, Any]) -> str:
        """Format a search result for use as context"""
        parts = []
        
        # Add source and verse information
        if result["chapter"] and result["verse"]:
            parts.append(f"Source: {result['source']} - Chapter {result['chapter']}, Verse {result['verse']}")
        else:
            parts.append(f"Source: {result['source']}")
        
        # Add Sanskrit if available
        if result.get("sanskrit"):
            parts.append(f"Sanskrit: {result['sanskrit']}")
        
        # Add translation if available
        if result.get("translation"):
            parts.append(f"Translation: {result['translation']}")
        
        # Add explanation if available
        if result.get("explanation"):
            parts.append(f"Commentary: {result['explanation']}")
        
        # Add the main text
        parts.append(f"Text: {result['text']}")
        
        return "\n".join(parts)
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database"""
        try:
            info = self.vector_store.get_collection_info()
            return {
                "total_documents": info.get("points_count", 0),
                "indexed_documents": info.get("indexed_vectors_count", 0),
                "status": info.get("status", "unknown")
            }
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"error": str(e)}
    
    def _is_hindu_text_related(self, question: str) -> bool:
        """Check if the question is related to Hindu texts - using a more permissive approach"""
        hindu_keywords = [
            'krishna', 'rama', 'ram', 'sita', 'hanuman', 'arjuna', 'dharma', 'karma', 'yoga', 'meditation',
            'bhagavad', 'gita', 'ramayana', 'mahabharata', 'vedas', 'upanishads', 'sanskrit',
            'moksha', 'nirvana', 'hindu', 'hinduism', 'spiritual', 'soul', 'atman', 'brahman',
            'vishnu', 'shiva', 'ganesha', 'devi', 'goddess', 'god', 'divine', 'sacred', 'holy',
            'temple', 'prayer', 'mantra', 'om', 'aum', 'patanjali', 'sage', 'guru', 'ashram',
            'verse', 'chapter', 'shloka', 'sutra', 'philosophy', 'truth', 'consciousness',
            'devotion', 'worship', 'faith', 'righteous', 'sin', 'virtue', 'ethics', 'duty',
            'life', 'death', 'rebirth', 'purpose', 'peace', 'happiness', 'suffering', 'wisdom',
            # Add common character names and relationships from texts
            'dasharatha', 'pita', 'mata', 'father', 'mother', 'son', 'daughter', 'brother', 'sister',
            'wife', 'husband', 'bharat', 'lakshmana', 'shatrughna', 'kaikeyi', 'kausalya', 'sumitra',
            'ravana', 'lakshman', 'bharata', 'mandodari', 'surpanakha', 'kumbhakarna', 'vibhishana',
            'pandava', 'kaurava', 'draupadi', 'yudhishthira', 'bhima', 'nakula', 'sahadeva',
            'duryodhana', 'dushasana', 'shakuni', 'gandhari', 'kunti', 'madri', 'pandu', 'dhritarashtra'
        ]
        
        question_lower = question.lower()
        
        # Check for Hindu-related keywords
        has_hindu_keywords = any(keyword in question_lower for keyword in hindu_keywords)
        
        # Check for modern/celebrity names that should be rejected - be more specific
        modern_keywords = [
            'salman khan', 'akshay kumar', 'shah rukh khan', 'bollywood', 'actor', 'actress', 'movie', 'film',
            'cricket', 'politics', 'politician', 'president', 'prime minister', 'covid', 'coronavirus',
            'technology', 'computer', 'internet', 'facebook', 'instagram', 'whatsapp', 'twitter',
            'stock market', 'cryptocurrency', 'bitcoin', 'business', 'company', 'startup',
            'sports', 'football', 'tennis', 'olympics', 'ipl', 'match', 'score'
        ]
        
        has_modern_keywords = any(keyword in question_lower for keyword in modern_keywords)
        
        # If it contains modern keywords, definitely not Hindu text related
        if has_modern_keywords:
            return False
        
        # Check for Hindi question patterns that are likely about Hindu texts
        hindi_patterns = [
            'kya naam', 'kaun', 'kahan', 'kaise', 'kyun', 'kya', 'ki', 'ka', 'ke',
            'naam tha', 'naam hai', 'kon tha', 'kon hai', 'kahan tha', 'kahan hai'
        ]
        
        has_hindi_patterns = any(pattern in question_lower for pattern in hindi_patterns)
        
        # More permissive approach - allow most philosophical and spiritual questions
        spiritual_patterns = [
            'what is', 'how to', 'meaning', 'significance', 'teaching', 'purpose of',
            'why do', 'how can', 'what does', 'tell me about', 'explain', 'describe',
            'who is', 'who was', 'where is', 'where was', 'when did'
        ]
        
        has_spiritual_patterns = any(pattern in question_lower for pattern in spiritual_patterns)
        
        # Accept if it has Hindu keywords, or if it's a Hindi question about characters/relationships,
        # or if it's a general spiritual/philosophical question
        return (has_hindu_keywords or 
                (has_hindi_patterns and len(question.strip()) > 5) or 
                (has_spiritual_patterns and len(question.strip()) > 10))

    def search_by_verse(self, chapter: str, verse: str) -> Dict[str, Any]:
        """Search for a specific verse"""
        try:
            # Deterministic metadata lookup — no unreliable semantic search needed
            result = self.vector_store.get_by_verse_id(chapter, verse)

            if result:
                return {
                    "found": True,
                    "sanskrit": result.get("sanskrit", ""),
                    "translation": result.get("translation", ""),
                    "explanation": result.get("explanation", ""),
                    "source": result.get("source", ""),
                    "chapter": result.get("chapter", ""),
                    "verse": result.get("verse", "")
                }
            else:
                return {"found": False}

        except Exception as e:
            logger.error(f"Error searching for verse {chapter}.{verse}: {e}")
            return {"found": False, "error": str(e)}
