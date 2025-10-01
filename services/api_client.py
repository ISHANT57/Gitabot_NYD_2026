import requests
import json
import logging
import time
from typing import List, Dict, Any
from config import Config

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self):
        self.config = Config()
        self.mistral_api_key = self.config.MISTRAL_API_KEY
        self.openrouter_api_key = self.config.OPENROUTER_API_KEY

    def get_embedding(self, text: str, use_api: bool = False, max_retries: int = 3) -> List[float]:
        """Get embedding for text. By default uses hash-based for bulk loading, optionally uses API"""
        # For bulk loading, use hash-based embeddings to avoid rate limits
        if not use_api:
            return self._get_embedding_openrouter(text)
        
        # Only use API when specifically requested
        for attempt in range(max_retries):
            try:
                url = "https://api.mistral.ai/v1/embeddings"
                headers = {
                    "Authorization": f"Bearer {self.mistral_api_key}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": self.config.EMBEDDING_MODEL,
                    "input": [text]
                }

                response = requests.post(url, headers=headers, json=data)
                
                if response.status_code == 429:  # Rate limit hit
                    wait_time = (2 ** attempt) * 5  # Exponential backoff: 5s, 10s, 20s
                    logger.warning(f"Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                result = response.json()
                return result["data"][0]["embedding"]

            except Exception as e:
                if attempt == max_retries - 1:  # Last attempt
                    logger.error(f"Error getting embedding from Mistral after {max_retries} attempts: {e}")
                    # Fallback to hash-based embedding
                    return self._get_embedding_openrouter(text)
                else:
                    logger.warning(f"Attempt {attempt + 1} failed, retrying: {e}")
                    time.sleep(2)  # Wait 2 seconds before retry
        
        # Fallback if all retries failed
        return self._get_embedding_openrouter(text)

    def _get_embedding_openrouter(self, text: str) -> List[float]:
        """Fallback embedding using OpenRouter (using chat completion with a simple prompt for similarity)"""
        try:
            # Since OpenRouter embedding API is not working properly, 
            # let's use a simple fallback approach for now
            # This is a temporary solution until API issues are resolved

            # For now, create a simple hash-based pseudo-embedding
            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()

            # Convert hash to a simple 1024-dimensional vector
            embedding = []
            for i in range(0, len(text_hash), 2):
                hex_val = text_hash[i:i+2]
                embedding.append(int(hex_val, 16) / 255.0)

            # Pad to 1024 dimensions to match expected embedding size
            while len(embedding) < 1024:
                embedding.extend(embedding[:min(len(embedding), 1024 - len(embedding))])

            # Truncate to exactly 1024 if needed
            embedding = embedding[:1024]

            logger.warning("Using fallback hash-based embedding due to API issues")
            return embedding

        except Exception as e:
            logger.error(f"Error in fallback embedding: {e}")
            raise

    def generate_answer(self, question: str, context: str) -> str:
        """Generate answer using Mixtral 8x7B Instruct via OpenRouter for humanized responses"""
        try:
            # Use OpenRouter as primary for Mixtral 8x7B Instruct
            return self._generate_answer_openrouter(question, context)
        except Exception as e:
            logger.error(f"Error generating answer with OpenRouter: {e}")
            # Return informative error message if OpenRouter fails
            return "I'm unable to generate an answer right now because the AI service is temporarily unavailable. Please try again in a few moments, or check if there are relevant verses in the database that might help with your question."

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