import pandas as pd
import json
import logging
from typing import List, Dict, Any, Tuple
import os
import re
from config import Config
from utils.text_utils import TextChunker

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.config = Config()
        self.chunker = TextChunker(
            chunk_size=self.config.CHUNK_SIZE,
            overlap=self.config.CHUNK_OVERLAP
        )
    
    def process_csv_file(self, filepath: str, source_name: str) -> List[Dict[str, Any]]:
        """Process CSV file and return list of document chunks"""
        try:
            df = pd.read_csv(filepath)
            logger.info(f"Processing CSV file: {filepath} with {len(df)} rows")
            
            documents = []
            
            for _, row in df.iterrows():
                # Extract fields based on CSV structure
                chapter = str(row.get('chapter', ''))
                verse = str(row.get('verse', ''))
                sanskrit_val = row.get('sanskrit')
                translation_val = row.get('translation')
                explanation_val = row.get('explanation') 
                question_val = row.get('question')
                
                sanskrit = str(sanskrit_val) if sanskrit_val is not None and pd.notna(sanskrit_val) else ''
                translation = str(translation_val) if translation_val is not None and pd.notna(translation_val) else ''
                explanation = str(explanation_val) if explanation_val is not None and pd.notna(explanation_val) else ''
                question = str(question_val) if question_val is not None and pd.notna(question_val) else ''
                
                # Create text content for embedding
                text_parts = []
                if sanskrit:
                    text_parts.append(f"Sanskrit: {sanskrit}")
                if translation:
                    text_parts.append(f"Translation: {translation}")
                if explanation:
                    text_parts.append(f"Explanation: {explanation}")
                if question:
                    text_parts.append(f"Related Question: {question}")
                
                text_content = "\n\n".join(text_parts)
                
                if text_content.strip():
                    # Create chunks if text is too long
                    chunks = self.chunker.chunk_text(text_content)
                    
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "text": chunk,
                            "source": source_name,
                            "chapter": chapter,
                            "verse": verse,
                            "sanskrit": sanskrit,
                            "translation": translation,
                            "explanation": explanation,
                            "metadata": {
                                "verse_id": f"{chapter}.{verse}",
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "has_question": bool(question),
                                "question": question
                            }
                        }
                        documents.append(doc)
            
            logger.info(f"Processed {len(documents)} document chunks from {filepath}")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing CSV file {filepath}: {e}")
            return []
    
    def process_json_file(self, filepath: str, source_name: str) -> List[Dict[str, Any]]:
        """Process JSON file with various formats and return list of document chunks"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            documents = []
            
            # Handle different JSON formats
            if isinstance(data, list):
                logger.info(f"Processing JSON array file: {filepath} with {len(data)} entries")
                documents = self._process_json_array(data, source_name)
            elif isinstance(data, dict):
                if "text" in data:
                    # Single text object format (Kanda files)
                    logger.info(f"Processing single text JSON file: {filepath}")
                    documents = self._process_single_text_json(data, source_name)
                elif "allowed_entities" in data:
                    # Character database format
                    logger.info(f"Processing character database: {filepath}")
                    documents = self._process_character_database(data, source_name)
                else:
                    logger.warning(f"Unknown JSON format in {filepath}")
            else:
                logger.warning(f"Unexpected JSON structure in {filepath}")
            
            logger.info(f"Processed {len(documents)} document chunks from {filepath}")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing JSON file {filepath}: {e}")
            return []
    
    def _process_json_array(self, data: List[Dict], source_name: str) -> List[Dict[str, Any]]:
        """Process JSON array format (verses, detailed content)"""
        documents = []
        
        for entry in data:
            # Handle verses-extracted format
            if "Kanda" in entry and "Sarga" in entry:
                documents.extend(self._process_verses_extracted_entry(entry, source_name))
            # Handle iyd_dataset format  
            elif "Book Name" in entry:
                documents.extend(self._process_iyd_dataset_entry(entry, source_name))
            # Handle original ramayana verses format
            elif "book_name" in entry:
                documents.extend(self._process_original_verses_entry(entry, source_name))
            else:
                logger.warning(f"Unknown array entry format in {source_name}")
        
        return documents
    
    def _process_verses_extracted_entry(self, entry: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Process verses-extracted format entry"""
        kanda = entry.get('Kanda', '')
        sarga = entry.get('Sarga', '')
        shloka = str(entry.get('Shloka', ''))
        original_text = entry.get('Original_Text', '')
        vector_input = entry.get('Vector_Input', '')
        
        # Use both original and vector input for comprehensive content
        text_parts = []
        if kanda:
            text_parts.append(f"Kanda: {kanda}")
        if sarga:
            text_parts.append(f"Sarga: {sarga}")
        if shloka:
            text_parts.append(f"Shloka: {shloka}")
        if original_text:
            text_parts.append(f"Original Text: {original_text}")
        if vector_input and vector_input != original_text.lower():
            text_parts.append(f"Processed Text: {vector_input}")
        
        text_content = "\n".join(text_parts)
        
        documents = []
        if text_content.strip():
            chunks = self.chunker.chunk_text(text_content)
            
            for i, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "source": source_name,
                    "chapter": sarga,
                    "verse": shloka,
                    "sanskrit": "",
                    "translation": original_text,
                    "explanation": "",
                    "metadata": {
                        "verse_id": f"{kanda}-{sarga}-{shloka}",
                        "kanda": kanda,
                        "sarga": sarga,
                        "shloka": shloka,
                        "vector_input": vector_input,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                documents.append(doc)
        
        return documents
    
    def _process_iyd_dataset_entry(self, entry: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Process iyd_dataset format entry"""
        book_name = entry.get('Book Name', '')
        chapter = str(entry.get('Chapter', ''))
        verse = str(entry.get('Verse', ''))
        content = entry.get('Content', '')
        
        text_parts = []
        if book_name:
            text_parts.append(f"Book: {book_name}")
        if chapter:
            text_parts.append(f"Chapter: {chapter}")
        if verse:
            text_parts.append(f"Verse: {verse}")
        if content:
            text_parts.append(f"Content: {content}")
        
        text_content = "\n".join(text_parts)
        
        documents = []
        if text_content.strip():
            chunks = self.chunker.chunk_text(text_content)
            
            for i, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "source": source_name,
                    "chapter": chapter,
                    "verse": verse,
                    "sanskrit": "",
                    "translation": content,
                    "explanation": "",
                    "metadata": {
                        "verse_id": f"{book_name}-{chapter}-{verse}",
                        "book_name": book_name,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                documents.append(doc)
        
        return documents
    
    def _process_original_verses_entry(self, entry: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Process original verses format entry"""
        book_name = entry.get('book_name', '')
        book_number = str(entry.get('book_number', ''))
        chapter_number = str(entry.get('chapter_number', ''))
        verse_number = entry.get('verse_number', [])
        verse_text = entry.get('verse', '')
        verse_id = entry.get('verse_id', '')
        
        # Handle verse numbers (can be a list)
        if isinstance(verse_number, list):
            verse_nums = ', '.join(str(v) for v in verse_number)
        else:
            verse_nums = str(verse_number)
        
        # Create comprehensive text content
        text_parts = []
        text_parts.append(f"Book: {book_name} ({book_number})")
        text_parts.append(f"Chapter: {chapter_number}")
        text_parts.append(f"Verse: {verse_nums}")
        text_parts.append(f"Text: {verse_text}")
        if verse_id:
            text_parts.append(f"Reference: {verse_id}")
        
        text_content = "\n".join(text_parts)
        
        documents = []
        if text_content.strip():
            chunks = self.chunker.chunk_text(text_content)
            
            for i, chunk in enumerate(chunks):
                doc = {
                    "text": chunk,
                    "source": source_name,
                    "chapter": chapter_number,
                    "verse": verse_nums,
                    "sanskrit": "",
                    "translation": verse_text,
                    "explanation": "",
                    "metadata": {
                        "verse_id": verse_id,
                        "book_name": book_name,
                        "book_number": book_number,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                }
                documents.append(doc)
        
        return documents
    
    def _process_single_text_json(self, data: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Process single text object format (Kanda files)"""
        text_content = data.get('text', '')
        documents = []
        
        if text_content:
            # Parse the structured text content
            sections = text_content.split('----------------------------------------')
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Extract chapter and verse information
                lines = section.split('\n')
                chapter = ""
                verse = ""
                content = ""
                
                for line in lines:
                    line = line.strip()
                    if line.startswith('Chapter:'):
                        chapter = line.replace('Chapter:', '').strip()
                    elif line.startswith('Verse:'):
                        verse = line.replace('Verse:', '').strip()
                    elif line.startswith('Content:'):
                        content = line.replace('Content:', '').strip()
                
                if content:
                    full_text = f"Chapter: {chapter}\nVerse: {verse}\nContent: {content}"
                    chunks = self.chunker.chunk_text(full_text)
                    
                    for i, chunk in enumerate(chunks):
                        doc = {
                            "text": chunk,
                            "source": source_name,
                            "chapter": chapter,
                            "verse": verse,
                            "sanskrit": "",
                            "translation": content,
                            "explanation": "",
                            "metadata": {
                                "verse_id": f"{chapter}-{verse}",
                                "chunk_index": i,
                                "total_chunks": len(chunks)
                            }
                        }
                        documents.append(doc)
        
        return documents
    
    def _process_character_database(self, data: Dict, source_name: str) -> List[Dict[str, Any]]:
        """Process character database format"""
        documents = []
        entities = data.get('allowed_entities', {})
        
        for char_name, char_info in entities.items():
            aliases = char_info.get('aliases', [])
            category = char_info.get('category', '')
            description = char_info.get('description', '')
            notes = char_info.get('notes', '')
            source = char_info.get('source', '')
            
            # Create comprehensive character information
            text_parts = []
            text_parts.append(f"Character: {char_name}")
            if aliases:
                text_parts.append(f"Also known as: {', '.join(aliases)}")
            if category:
                text_parts.append(f"Category: {category}")
            if description:
                text_parts.append(f"Description: {description}")
            if notes:
                text_parts.append(f"Additional Notes: {notes}")
            if source:
                text_parts.append(f"Source: {source}")
            
            text_content = "\n".join(text_parts)
            
            if text_content.strip():
                chunks = self.chunker.chunk_text(text_content)
                
                for i, chunk in enumerate(chunks):
                    doc = {
                        "text": chunk,
                        "source": source_name,
                        "chapter": "",
                        "verse": "",
                        "sanskrit": "",
                        "translation": description,
                        "explanation": notes,
                        "metadata": {
                            "character_name": char_name,
                            "aliases": aliases,
                            "category": category,
                            "character_source": source,
                            "chunk_index": i,
                            "total_chunks": len(chunks)
                        }
                    }
                    documents.append(doc)
        
        return documents
    
    def process_txt_file(self, filepath: str, source_name: str) -> List[Dict[str, Any]]:
        """Process TXT file and return list of document chunks"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"Processing TXT file: {filepath}")
            
            # Parse the text file structure (Gita edition format)
            documents = []
            current_chapter = ""
            current_verse = ""
            current_text = ""
            current_sanskrit = ""
            
            lines = content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Check for chapter header
                if line.startswith('Chapter-') or line.startswith('CHAPTER'):
                    current_chapter = self._extract_chapter_number(line)
                    i += 1
                    continue
                
                # Check for text number (verse)
                if line.startswith('TEXT '):
                    current_verse = self._extract_verse_number(line)
                    i += 1
                    
                    # Collect Sanskrit text
                    sanskrit_lines = []
                    while i < len(lines) and not lines[i].strip().startswith('TRANSLATION'):
                        if lines[i].strip() and not lines[i].strip().startswith('TEXT'):
                            sanskrit_lines.append(lines[i].strip())
                        i += 1
                    
                    current_sanskrit = ' '.join(sanskrit_lines)
                    
                    # Skip to translation
                    if i < len(lines) and lines[i].strip().startswith('TRANSLATION'):
                        i += 1
                        
                        # Collect translation and purport
                        content_lines = []
                        while i < len(lines) and not lines[i].strip().startswith('TEXT '):
                            if lines[i].strip():
                                content_lines.append(lines[i].strip())
                            i += 1
                        
                        current_text = ' '.join(content_lines)
                        
                        # Create document
                        if current_text and current_chapter and current_verse:
                            full_text = f"Chapter {current_chapter}, Verse {current_verse}\n\n"
                            if current_sanskrit:
                                full_text += f"Sanskrit: {current_sanskrit}\n\n"
                            full_text += f"Translation and Commentary: {current_text}"
                            
                            chunks = self.chunker.chunk_text(full_text)
                            
                            for j, chunk in enumerate(chunks):
                                doc = {
                                    "text": chunk,
                                    "source": source_name,
                                    "chapter": current_chapter,
                                    "verse": current_verse,
                                    "sanskrit": current_sanskrit,
                                    "translation": current_text,
                                    "explanation": "",
                                    "metadata": {
                                        "verse_id": f"{current_chapter}.{current_verse}",
                                        "chunk_index": j,
                                        "total_chunks": len(chunks)
                                    }
                                }
                                documents.append(doc)
                        continue
                
                i += 1
            
            logger.info(f"Processed {len(documents)} document chunks from {filepath}")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing TXT file {filepath}: {e}")
            return []
    
    def _extract_chapter_number(self, text: str) -> str:
        """Extract chapter number from text"""
        match = re.search(r'(\d+)', text)
        return match.group(1) if match else ""
    
    def _extract_verse_number(self, text: str) -> str:
        """Extract verse number from text"""
        match = re.search(r'TEXT\s+(\d+)', text)
        return match.group(1) if match else ""
    
    def process_all_files(self) -> List[Dict[str, Any]]:
        """Process all data files"""
        all_documents = []
        data_files = self.config.get_data_files()
        
        for source_name, filename in data_files.items():
            filepath = os.path.join(self.config.DATA_DIR, filename)
            
            if not os.path.exists(filepath):
                logger.warning(f"File not found: {filepath}")
                continue
            
            if filename.endswith('.csv'):
                docs = self.process_csv_file(filepath, source_name)
            elif filename.endswith('.txt'):
                docs = self.process_txt_file(filepath, source_name)
            elif filename.endswith('.json'):
                docs = self.process_json_file(filepath, source_name)
            else:
                logger.warning(f"Unsupported file format: {filename}")
                continue
            
            all_documents.extend(docs)
        
        logger.info(f"Total processed documents: {len(all_documents)}")
        return all_documents
