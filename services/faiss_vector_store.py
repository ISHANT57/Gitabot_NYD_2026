import faiss
import numpy as np
import json
import os
import sqlite3
import threading
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Fields mirrored into SQLite columns (everything else goes in the JSON "metadata" blob).
_COLUMNS = ["text", "source", "chapter", "verse", "sanskrit", "translation", "explanation"]


class FaissVectorStore:
    """Low-memory vector store.

    - Vectors: 8-bit scalar-quantized FAISS index (~4x smaller than float32 flat),
      so a 45k x 1024 index is ~47 MB in RAM instead of ~187 MB.
    - Metadata: on-disk SQLite database (only the ~20 hit rows per query are read),
      instead of loading a large JSON list fully into memory.

    This keeps the runtime footprint small enough for a 512 MB instance.
    """

    def __init__(self, embedding_dim=1024, index_file="vector_index.faiss", db_file="metadata.db"):
        self.embedding_dim = embedding_dim
        self.index_file = index_file
        self.db_file = db_file
        self.is_available = True
        self._lock = threading.Lock()

        self.index = self._new_index()
        self._conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self._init_db()
        self._load_index()

        logger.info(
            f"FAISS vector store initialized: {self.index.ntotal} vectors, "
            f"{self._count_rows()} metadata rows"
        )

    # ── setup ──────────────────────────────────────────────────────────────
    def _new_index(self):
        """8-bit scalar-quantized index with inner-product (cosine) metric."""
        return faiss.IndexScalarQuantizer(
            self.embedding_dim, faiss.ScalarQuantizer.QT_8bit, faiss.METRIC_INNER_PRODUCT
        )

    def _init_db(self):
        cols = ", ".join(f"{c} TEXT" for c in _COLUMNS)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS docs (id INTEGER PRIMARY KEY, {cols}, meta TEXT)"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_chapter_verse ON docs(chapter, verse)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON docs(source)")
        self._conn.commit()

    def _load_index(self):
        try:
            if os.path.exists(self.index_file):
                self.index = faiss.read_index(self.index_file)
                logger.info(f"Loaded existing index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.warning(f"Could not load existing index: {e}")
            self.index = self._new_index()

    def _count_rows(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) FROM docs")
            return cur.fetchone()[0]

    def _save_index(self):
        try:
            faiss.write_index(self.index, self.index_file)
            self._conn.commit()
            logger.info("Index and metadata saved successfully")
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    # ── writes ─────────────────────────────────────────────────────────────
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents (each must carry an 'embedding') to the store."""
        try:
            embeddings = []
            rows = []
            next_id = self.index.ntotal

            for doc in documents:
                if "embedding" not in doc:
                    logger.warning("Document missing embedding, skipping")
                    continue

                embedding = np.array(doc["embedding"], dtype=np.float32)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                embeddings.append(embedding)

                row = [next_id + len(rows)]
                row += [str(doc.get(c, "") or "") for c in _COLUMNS]
                row.append(json.dumps(doc.get("metadata", {}), ensure_ascii=False))
                rows.append(tuple(row))

            if not embeddings:
                return

            arr = np.array(embeddings, dtype=np.float32)

            # Scalar quantizer must be trained before the first add.
            if not self.index.is_trained:
                logger.info(f"Training scalar quantizer on {len(arr)} vectors...")
                self.index.train(arr)

            self.index.add(arr)

            placeholders = ", ".join(["?"] * (len(_COLUMNS) + 2))  # id + columns + meta
            with self._lock:
                self._conn.executemany(f"INSERT INTO docs VALUES ({placeholders})", rows)
                self._conn.commit()

            self._save_index()
            logger.info(f"Added {len(embeddings)} documents to vector store")

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    def clear_collection(self):
        try:
            self.index = self._new_index()
            with self._lock:
                self._conn.execute("DELETE FROM docs")
                self._conn.commit()
            self._save_index()
            logger.info("Collection cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    # ── reads ──────────────────────────────────────────────────────────────
    def _row_to_dict(self, row) -> Dict[str, Any]:
        d = {c: row[i + 1] for i, c in enumerate(_COLUMNS)}
        try:
            d["metadata"] = json.loads(row[len(_COLUMNS) + 1]) if row[len(_COLUMNS) + 1] else {}
        except Exception:
            d["metadata"] = {}
        return d

    def _get_rows(self, ids: List[int]) -> Dict[int, Any]:
        if not ids:
            return {}
        placeholders = ", ".join(["?"] * len(ids))
        with self._lock:
            cur = self._conn.execute(
                f"SELECT * FROM docs WHERE id IN ({placeholders})", ids
            )
            return {r[0]: r for r in cur.fetchall()}

    def search(self, query_embedding: List[float], limit: int = 10, source_filter=None) -> List[Dict[str, Any]]:
        try:
            if self.index.ntotal == 0:
                logger.warning("No documents in vector store")
                return []

            query_vec = np.array(query_embedding, dtype=np.float32).reshape(1, -1)
            norm = np.linalg.norm(query_vec)
            if norm > 0:
                query_vec = query_vec / norm

            # Over-fetch to allow for source filtering
            k = min(max(limit * 3, limit), self.index.ntotal)
            scores, indices = self.index.search(query_vec, k)

            ordered_ids = [int(idx) for idx in indices[0] if idx >= 0]
            rows = self._get_rows(ordered_ids)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                idx = int(idx)
                if idx < 0 or idx not in rows:
                    continue

                result = self._row_to_dict(rows[idx])

                if source_filter:
                    doc_source = result.get("source", "")
                    if isinstance(source_filter, list):
                        if doc_source not in source_filter:
                            continue
                    elif doc_source != source_filter:
                        continue

                result["score"] = float(score)
                results.append(result)
                if len(results) >= limit:
                    break

            logger.info(f"Found {len(results)} similar documents")
            return results

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    def get_by_verse_id(self, chapter: str, verse: str) -> Optional[Dict[str, Any]]:
        """Deterministic verse lookup by chapter/verse (or nested verse_id)."""
        verse_id = f"{chapter}.{verse}"
        try:
            with self._lock:
                cur = self._conn.execute(
                    "SELECT * FROM docs WHERE chapter = ? AND verse = ? LIMIT 1",
                    (str(chapter), str(verse)),
                )
                row = cur.fetchone()
            if row:
                return self._row_to_dict(row)

            # Fallback: scan for a nested metadata verse_id match
            with self._lock:
                cur = self._conn.execute("SELECT * FROM docs WHERE meta LIKE ?", (f'%"{verse_id}"%',))
                for row in cur.fetchall():
                    d = self._row_to_dict(row)
                    if d.get("metadata", {}).get("verse_id") == verse_id:
                        return d
            return None
        except Exception as e:
            logger.error(f"Error in get_by_verse_id: {e}")
            return None

    def get_collection_info(self) -> Dict[str, Any]:
        return {
            "vectors_count": self.index.ntotal,
            "indexed_vectors_count": self.index.ntotal,
            "points_count": self._count_rows(),
            "status": "available",
        }
