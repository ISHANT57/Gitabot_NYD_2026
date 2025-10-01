import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse
from config import Config

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.collection_name = self.config.QDRANT_COLLECTION_NAME
        self.is_available = False
        
        try:
            self.client = QdrantClient(
                url=self.config.QDRANT_URL,
                api_key=self.config.QDRANT_API_KEY
            )
            self._ensure_collection_exists()
            self.is_available = True
            logger.info("Vector store initialized successfully")
        except Exception as e:
            logger.warning(f"Vector store not available: {e}")
            logger.info("Application will run without vector database functionality")
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists in Qdrant"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Creating collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1024,  # Mistral embedding dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Collection {self.collection_name} created successfully")
            else:
                logger.info(f"Collection {self.collection_name} already exists")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store"""
        if not self.is_available:
            logger.warning("Vector store not available - cannot add documents")
            return
            
        try:
            points = []
            for i, doc in enumerate(documents):
                point = PointStruct(
                    id=i,
                    vector=doc["embedding"],
                    payload={
                        "text": doc["text"],
                        "source": doc.get("source", ""),
                        "chapter": doc.get("chapter", ""),
                        "verse": doc.get("verse", ""),
                        "sanskrit": doc.get("sanskrit", ""),
                        "translation": doc.get("translation", ""),
                        "explanation": doc.get("explanation", ""),
                        "metadata": doc.get("metadata", {})
                    }
                )
                points.append(point)
            
            # Batch upload points
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points) + batch_size - 1)//batch_size}")
            
            logger.info(f"Successfully added {len(documents)} documents to vector store")
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def search(self, query_embedding: List[float], limit: int = 10, source_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.is_available:
            logger.warning("Vector store not available - cannot search")
            return []
            
        try:
            search_filter = None
            if source_filter:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=source_filter)
                        )
                    ]
                )
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=search_filter,
                score_threshold=self.config.SIMILARITY_THRESHOLD
            )
            
            results = []
            for hit in search_result:
                result = {
                    "text": hit.payload.get("text", ""),
                    "source": hit.payload.get("source", ""),
                    "chapter": hit.payload.get("chapter", ""),
                    "verse": hit.payload.get("verse", ""),
                    "sanskrit": hit.payload.get("sanskrit", ""),
                    "translation": hit.payload.get("translation", ""),
                    "explanation": hit.payload.get("explanation", ""),
                    "score": hit.score,
                    "metadata": hit.payload.get("metadata", {})
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        if not self.is_available:
            return {
                "vectors_count": 0,
                "indexed_vectors_count": 0,
                "points_count": 0,
                "status": "unavailable"
            }
            
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        if not self.is_available:
            logger.warning("Vector store not available - cannot clear collection")
            return
            
        try:
            self.client.delete_collection(self.collection_name)
            self._ensure_collection_exists()
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
