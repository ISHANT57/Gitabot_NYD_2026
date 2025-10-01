import faiss
import numpy as np
import json
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class FaissVectorStore:
    def __init__(self, embedding_dim=1024, index_file="vector_index.faiss", metadata_file="metadata.json"):
        self.embedding_dim = embedding_dim
        self.index_file = index_file
        self.metadata_file = metadata_file
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner product for cosine similarity
        self.metadata = []
        self.is_available = True
        
        # Load existing index if available
        self._load_index()
        logger.info(f"FAISS vector store initialized with {self.index.ntotal} vectors")
    
    def _load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
                self.index = faiss.read_index(self.index_file)
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded existing index with {len(self.metadata)} documents")
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            logger.info("Index and metadata saved successfully")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        try:
            embeddings = []
            metadata_batch = []
            
            for doc in documents:
                if "embedding" not in doc:
                    logger.warning("Document missing embedding, skipping")
                    continue
                
                # Normalize embeddings for cosine similarity
                embedding = np.array(doc["embedding"], dtype=np.float32)
                embedding = embedding / np.linalg.norm(embedding)
                embeddings.append(embedding)
                
                # Store metadata
                metadata_entry = {
                    "text": doc.get("text", ""),
                    "source": doc.get("source", ""),
                    "chapter": doc.get("chapter", ""),
                    "verse": doc.get("verse", ""),
                    "sanskrit": doc.get("sanskrit", ""),
                    "translation": doc.get("translation", ""),
                    "explanation": doc.get("explanation", ""),
                    "metadata": doc.get("metadata", {})
                }
                metadata_batch.append(metadata_entry)
            
            if embeddings:
                embeddings_array = np.array(embeddings, dtype=np.float32)
                self.index.add(embeddings_array)
                self.metadata.extend(metadata_batch)
                self._save_index()
                
                logger.info(f"Added {len(embeddings)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(self, query_embedding: List[float], limit: int = 10, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            if self.index.ntotal == 0:
                logger.warning("No documents in vector store")
                return []
            
            # Normalize query embedding
            query_vec = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            query_vec = query_vec / np.linalg.norm(query_vec)
            
            # Search
            scores, indices = self.index.search(query_vec, min(limit * 2, self.index.ntotal))  # Get more for filtering
            
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.metadata):
                    metadata = self.metadata[idx]
                    
                    # Apply source filter if specified
                    if source_filter and metadata.get("source", "") != source_filter:
                        continue
                    
                    result = {
                        "text": metadata.get("text", ""),
                        "source": metadata.get("source", ""),
                        "chapter": metadata.get("chapter", ""),
                        "verse": metadata.get("verse", ""),
                        "sanskrit": metadata.get("sanskrit", ""),
                        "translation": metadata.get("translation", ""),
                        "explanation": metadata.get("explanation", ""),
                        "score": float(score),
                        "metadata": metadata.get("metadata", {})
                    }
                    results.append(result)
                    
                    if len(results) >= limit:
                        break
            
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        return {
            "vectors_count": self.index.ntotal,
            "indexed_vectors_count": self.index.ntotal,
            "points_count": len(self.metadata),
            "status": "available"
        }
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
            self.metadata = []
            self._save_index()
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise