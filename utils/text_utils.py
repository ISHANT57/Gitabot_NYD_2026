import re
from typing import List

class TextChunker:
    def __init__(self, chunk_size: int = 400, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text or len(text) < self.chunk_size:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this is not the last chunk, try to break at sentence boundary
            if end < len(text):
                # Look for sentence ending within the overlap region
                sentence_end = self._find_sentence_boundary(text, end - self.overlap, end)
                if sentence_end > start:
                    end = sentence_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = max(start + 1, end - self.overlap)
            
            # Break if we're not making progress
            if start >= len(text):
                break
        
        return chunks
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """Find the best sentence boundary within the given range"""
        # Look for sentence endings (., !, ?, ||)
        sentence_pattern = r'[.!?।॥]\s+'
        
        # Search backwards from end to start
        for match in re.finditer(sentence_pattern, text[start:end]):
            return start + match.end()
        
        # If no sentence boundary found, look for other boundaries
        # Look for paragraph breaks
        paragraph_match = re.search(r'\n\s*\n', text[start:end])
        if paragraph_match:
            return start + paragraph_match.end()
        
        # Look for clause boundaries
        clause_pattern = r'[,;]\s+'
        for match in re.finditer(clause_pattern, text[start:end]):
            return start + match.end()
        
        # Return original end if no good boundary found
        return end

class TextNormalizer:
    @staticmethod
    def normalize_sanskrit(text: str) -> str:
        """Normalize Sanskrit text for better processing"""
        if not text:
            return text
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Handle common Sanskrit punctuation
        text = text.replace('।', '.')
        text = text.replace('॥', '||')
        
        return text
    
    @staticmethod
    def normalize_query(query: str) -> str:
        """Normalize user query for better matching"""
        if not query:
            return query
        
        # Convert to lowercase for better matching
        query = query.lower().strip()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        
        return query
    
    @staticmethod
    def extract_verse_reference(text: str) -> str:
        """Extract verse reference (chapter.verse) from text"""
        # Look for patterns like "1.1", "Chapter 1 Verse 2", etc.
        patterns = [
            r'(\d+)\.(\d+)',
            r'chapter\s+(\d+)\s+verse\s+(\d+)',
            r'ch\.\s*(\d+)\s*v\.\s*(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                if len(match.groups()) == 2:
                    return f"{match.group(1)}.{match.group(2)}"
        
        return ""
