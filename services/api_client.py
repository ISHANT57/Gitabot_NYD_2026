import requests
import json
import logging
import time
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

# How many texts to send to the embeddings API per request during bulk indexing.
EMBED_BATCH_SIZE = 64
EMBED_DIM = 1024  # mistral-embed output dimension (must match the FAISS store)


class APIClient:
    def __init__(self):
        self.config = Config()
        self.mistral_api_key = self.config.MISTRAL_API_KEY
        self.openrouter_api_key = self.config.OPENROUTER_API_KEY
        self.gemini_api_key = self.config.GEMINI_API_KEY
        self.groq_api_key = self.config.GROQ_API_KEY

    def _mistral_key_valid(self) -> bool:
        """True only when a real Mistral key is configured (not the placeholder)."""
        return bool(self.mistral_api_key) and self.mistral_api_key != "default_mistral_key"

    def get_embedding(self, text: str, use_api: bool = True, max_retries: int = 5) -> List[float]:
        """Get a single embedding. Uses the real Mistral API by default so that the
        query is embedded the same way as the indexed documents."""
        return self.get_embeddings([text], use_api=use_api, max_retries=max_retries)[0]

    def get_embeddings(self, texts: List[str], use_api: bool = True,
                       max_retries: int = 5) -> List[List[float]]:
        """Embed a list of texts. Batches requests to the Mistral embeddings API.

        Falls back to the (low-quality) hash embedding ONLY when no real key is
        configured or the API keeps failing — and logs loudly when it does, since
        hash embeddings make semantic search meaningless.
        """
        if not texts:
            return []

        if not use_api or not self._mistral_key_valid():
            if use_api and not self._mistral_key_valid():
                logger.warning(
                    "MISTRAL_API_KEY not configured — falling back to LOW-QUALITY hash "
                    "embeddings. Semantic search will not work properly until a real key is set."
                )
            return [self._get_embedding_hash(t) for t in texts]

        results: List[List[float]] = []
        total = len(texts)
        for start in range(0, total, EMBED_BATCH_SIZE):
            batch = texts[start:start + EMBED_BATCH_SIZE]
            results.extend(self._embed_batch_mistral(batch, max_retries))
            if total > EMBED_BATCH_SIZE and (start + EMBED_BATCH_SIZE) % (EMBED_BATCH_SIZE * 20) == 0:
                logger.info(f"Embedded {min(start + EMBED_BATCH_SIZE, total)}/{total} texts")
        return results

    def _embed_batch_mistral(self, batch: List[str], max_retries: int) -> List[List[float]]:
        """Embed one batch via the Mistral API, with exponential backoff on rate limits."""
        url = "https://api.mistral.ai/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.mistral_api_key}",
            "Content-Type": "application/json",
        }
        data = {"model": self.config.EMBEDDING_MODEL, "input": batch}

        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=60)

                if response.status_code == 429:  # Rate limit hit
                    wait_time = (2 ** attempt) * 5  # 5s, 10s, 20s, ...
                    logger.warning(
                        f"Embedding rate limit hit, waiting {wait_time}s "
                        f"(retry {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                result = response.json()
                # Sort by index to guarantee the order matches the input batch
                items = sorted(result["data"], key=lambda x: x["index"])
                return [item["embedding"] for item in items]

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        f"Embedding batch failed after {max_retries} attempts ({e}); "
                        f"falling back to hash embeddings for this batch."
                    )
                    return [self._get_embedding_hash(t) for t in batch]
                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(2 ** attempt)

        return [self._get_embedding_hash(t) for t in batch]

    def _get_embedding_hash(self, text: str) -> List[float]:
        """Deterministic hash-based pseudo-embedding. LAST-RESORT FALLBACK ONLY.

        This carries no semantic meaning and should never be the primary path —
        it exists so the app degrades to something rather than crashing when the
        embedding API is unavailable.
        """
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()

        embedding: List[float] = []
        for i in range(0, len(text_hash), 2):
            hex_val = text_hash[i:i + 2]
            embedding.append(int(hex_val, 16) / 255.0)

        # Pad/truncate to the expected dimension
        while len(embedding) < EMBED_DIM:
            embedding.extend(embedding[:min(len(embedding), EMBED_DIM - len(embedding))])
        return embedding[:EMBED_DIM]

    def _groq_key_valid(self) -> bool:
        return bool(self.groq_api_key) and self.groq_api_key != "default_groq_key"

    def _gemini_key_valid(self) -> bool:
        return bool(self.gemini_api_key) and self.gemini_api_key != "default_gemini_key"

    def _openrouter_key_valid(self) -> bool:
        return bool(self.openrouter_api_key) and self.openrouter_api_key != "default_openrouter_key"

    _SYSTEM_PROMPT = """You are a knowledgeable assistant for Hindu religious texts including the Bhagavad Gita, Ramayana, Mahabharata, and Yoga Sutras.

INSTRUCTIONS:
- Answer questions directly with facts from Hindu religious texts
- Be respectful of the spiritual nature of these texts
- Provide clear, direct answers without any source citations, book references, or location mentions
- Do not mention where information can be found (no "found in", "mentioned in", "according to")
- Focus only on the factual content from the texts
- Give concise, informative answers

Your goal is to provide direct factual answers about Hindu texts, teachings, characters, and concepts."""

    def _build_user_prompt(self, question: str, context: str) -> str:
        return f"""Sacred Text Context:
{context}

Question: {question}

Answer directly with facts only, without mentioning sources or locations."""

    def generate_answer(self, question: str, context: str) -> str:
        """Generate an answer from the retrieved context.

        Tries configured providers in order (Groq -> Gemini -> OpenRouter), moving
        on to the next if one has no key or fails. Groq is primary because of its
        fast, generous free tier.
        """
        providers = [
            ("Groq", self._groq_key_valid, self._generate_answer_groq),
            ("Gemini", self._gemini_key_valid, self._generate_answer_gemini),
            ("OpenRouter", self._openrouter_key_valid, self._generate_answer_openrouter),
        ]

        any_key = False
        for name, key_valid, generate in providers:
            if not key_valid():
                continue
            any_key = True
            try:
                return generate(question, context)
            except Exception as e:
                logger.error(f"{name} answer generation failed: {e}")
                continue

        if not any_key:
            logger.error("No answer-generation key configured (set GROQ_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY)")

        return "I'm unable to generate an answer right now because the AI service is temporarily unavailable. Please try again in a few moments, or check if there are relevant verses in the database that might help with your question."

    def _generate_answer_groq(self, question: str, context: str) -> str:
        """Generate an answer using Groq (OpenAI-compatible chat completions API)."""
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.config.GROQ_MODEL,
            "messages": [
                {"role": "system", "content": self._SYSTEM_PROMPT},
                {"role": "user", "content": self._build_user_prompt(question, context)},
            ],
            "temperature": 0.4,
            "max_tokens": 1200,
        }

        server_errors = {500, 502, 503, 504}
        max_retries = 3
        for attempt in range(max_retries):
            response = requests.post(url, headers=headers, json=data, timeout=30)

            if response.status_code == 429:
                if attempt == 0:
                    logger.warning("Groq 429 (rate limit), one quick retry in 1s")
                    time.sleep(1)
                    continue
                raise RuntimeError("Groq rate limit / quota exhausted")

            if response.status_code in server_errors and attempt < max_retries - 1:
                time.sleep(attempt + 1)
                continue

            response.raise_for_status()
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            if not text:
                raise ValueError(f"Groq returned empty content: {result}")
            return text

        raise RuntimeError("Groq unavailable after retries")

    def _generate_answer_gemini(self, question: str, context: str) -> str:
        """Generate an answer using Google Gemini."""
        model = self.config.GEMINI_MODEL
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.gemini_api_key}"
        )
        headers = {"Content-Type": "application/json"}
        data = {
            "system_instruction": {"parts": [{"text": self._SYSTEM_PROMPT}]},
            "contents": [
                {"role": "user", "parts": [{"text": self._build_user_prompt(question, context)}]}
            ],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 1200},
        }

        # Keep total added latency small — this runs inside a web request, so a long
        # blocking retry loop would tie up the worker and stall other requests.
        # - 5xx server overload: retry briefly (usually recovers).
        # - 429: could be a short per-minute limit OR an exhausted daily quota. Retrying
        #   a daily-quota 429 is futile and would just block, so we try at most once quickly.
        server_errors = {500, 502, 503, 504}
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)

                if response.status_code == 429:
                    if attempt == 0:
                        logger.warning("Gemini 429 (rate/quota), one quick retry in 1s")
                        time.sleep(1)
                        continue
                    logger.error("Gemini 429 persists — quota likely exhausted; giving up fast")
                    raise RuntimeError("Gemini rate limit / quota exhausted")

                if response.status_code in server_errors:
                    if attempt < max_retries - 1:
                        wait_time = attempt + 1  # 1s, 2s
                        logger.warning(
                            f"Gemini {response.status_code}, retrying in {wait_time}s "
                            f"({attempt + 1}/{max_retries})"
                        )
                        time.sleep(wait_time)
                        continue
                    raise RuntimeError(f"Gemini server error {response.status_code}")

                response.raise_for_status()
                result = response.json()

                candidates = result.get("candidates", [])
                if not candidates:
                    raise ValueError(f"Gemini returned no candidates: {result}")
                parts = candidates[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
                if not text:
                    raise ValueError(f"Gemini returned empty text: {result}")
                return text

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(attempt + 1)
                    continue
                raise
        raise RuntimeError("Gemini unavailable after retries")

        # Exhausted retries on transient status codes
        raise RuntimeError(f"Gemini unavailable after {max_retries} attempts (last status transient)")

    def _generate_answer_openrouter(self, question: str, context: str) -> str:
        """Generate humanized answer using Mixtral 8x7B Instruct via OpenRouter"""
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json"
            }

            system_prompt = """You are a knowledgeable assistant for Hindu religious texts including the Bhagavad Gita, Ramayana, Mahabharata, and Yoga Sutras.

INSTRUCTIONS:
- Answer questions directly with facts from Hindu religious texts
- Be respectful of the spiritual nature of these texts
- Provide clear, direct answers without any source citations, book references, or location mentions
- Do not mention where information can be found (no "found in", "mentioned in", "according to")
- Focus only on the factual content from the texts
- Give concise, informative answers

Your goal is to provide direct factual answers about Hindu texts, teachings, characters, and concepts."""

            user_prompt = f"""Sacred Text Context:
{context}

Question: {question}

Answer directly with facts only, without mentioning sources or locations."""

            data = {
                "model": self.config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 1200
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except Exception as e:
            logger.error(f"Error generating answer with OpenRouter: {e}")
            raise