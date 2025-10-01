#!/usr/bin/env python3
"""
Backend-only chatbot using the existing RAG infrastructure.
This script provides a command-line interface to interact with the 
indexed documents and pretrained model.
"""

import os
import sys
import logging
import argparse
from typing import Optional

# Add the current directory to Python path to import our services
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import RAGService
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BackendChatbot:
    """Backend-only chatbot that processes queries using RAG services"""
    
    def __init__(self):
        """Initialize the chatbot with RAG service"""
        self.config = Config()
        self.rag_service = RAGService()
        self.initialized = False
        self._check_api_setup()
    
    def _check_api_setup(self):
        """Check if API keys are properly configured for local setup"""
        missing_keys = []
        
        if not self.config.OPENROUTER_API_KEY or self.config.OPENROUTER_API_KEY == "default_openrouter_key":
            missing_keys.append("OPENROUTER_API_KEY")
        
        if missing_keys:
            print("⚠️  API Configuration Issue Detected!")
            print("\nFor full functionality, you need to set these environment variables:")
            for key in missing_keys:
                print(f"  export {key}=your_api_key_here")
            
            print(f"\n📖 To get an OpenRouter API key:")
            print(f"  1. Visit: https://openrouter.ai/")
            print(f"  2. Sign up and get your API key")
            print(f"  3. Set the environment variable:")
            if os.name == 'nt':  # Windows
                print(f"     Windows: set OPENROUTER_API_KEY=your_key_here")
            else:  # Unix/Linux/macOS
                print(f"     Unix/Linux: export OPENROUTER_API_KEY=your_key_here")
            
            print(f"\n💡 Without API keys, the chatbot can still:")
            print(f"  ✅ Search and analyze your 45,784 documents")
            print(f"  ✅ Find relevant passages for your questions") 
            print(f"  ❌ Generate AI-powered answers (requires API key)")
            print()
        
    def initialize_database(self, force_reload: bool = False):
        """Initialize the database with all documents"""
        try:
            print("🔄 Initializing database with documents...")
            self.rag_service.initialize_database(force_reload=force_reload)
            self.initialized = True
            
            # Get stats to confirm initialization
            stats = self.rag_service.get_database_stats()
            print(f"✅ Database initialized successfully!")
            print(f"📊 Database contains {stats.get('total_documents', 0)} documents")
            print(f"📚 Sources: {', '.join(stats.get('sources', []))}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            print(f"❌ Failed to initialize database: {e}")
            return False
        return True
    
    def get_database_stats(self):
        """Get and display database statistics"""
        try:
            stats = self.rag_service.get_database_stats()
            print("\n📊 Database Statistics:")
            print(f"Total Documents: {stats.get('total_documents', 0)}")
            print(f"Sources: {', '.join(stats.get('sources', []))}")
            if 'source_counts' in stats:
                print("Documents per source:")
                for source, count in stats['source_counts'].items():
                    print(f"  - {source}: {count}")
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            print(f"❌ Failed to get database stats: {e}")
    
    def search_by_verse(self, chapter: str, verse: str):
        """Search for a specific verse"""
        try:
            result = self.rag_service.search_by_verse(chapter, verse)
            
            if result.get('found'):
                print(f"\n📖 Verse {chapter}.{verse}:")
                print(f"Sanskrit: {result.get('sanskrit', 'N/A')}")
                print(f"Translation: {result.get('translation', 'N/A')}")
                print(f"Explanation: {result.get('explanation', 'N/A')}")
                print(f"Source: {result.get('source', 'N/A')}")
            else:
                print(f"❌ Verse {chapter}.{verse} not found")
                
        except Exception as e:
            logger.error(f"Error searching for verse {chapter}.{verse}: {e}")
            print(f"❌ Error searching for verse: {e}")
    
    def answer_question(self, question: str, source_filter: Optional[str] = None):
        """Answer a question using the RAG system"""
        try:
            print(f"\n🤔 Question: {question}")
            print("🔍 Searching for relevant information...")
            
            result = self.rag_service.search_and_answer(question, source_filter)
            answer = result.get('answer', 'No answer generated')
            
            # Check if this is an API error message
            if "AI service is temporarily unavailable" in answer:
                print(f"\n⚠️  {answer}")
                # Show the relevant passages that were found
                if 'context' in result and result['context']:
                    print(f"\n📖 However, I found {len(result['context'])} relevant passages from your texts:")
                    self._display_relevant_passages(result['context'][:3])
                else:
                    print("🔍 Try rephrasing your question or check the database initialization.")
            else:
                print(f"\n🤖 Answer: {answer}")
                
                # Show relevant sources if available
                if 'context' in result and result['context']:
                    print(f"\n📚 Based on {len(result['context'])} relevant passages:")
                    for i, doc in enumerate(result['context'][:3], 1):  # Show top 3 sources
                        source_info = f"{doc.get('source', 'Unknown')}"
                        if doc.get('chapter') and doc.get('verse'):
                            source_info += f" ({doc['chapter']}.{doc['verse']})"
                        print(f"  {i}. {source_info}")
            
            if 'confidence' in result:
                confidence = result['confidence']
                print(f"🎯 Confidence: {confidence:.1%}")
                
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            print(f"❌ Error processing question: {e}")
    
    def _display_relevant_passages(self, passages):
        """Display relevant text passages when API is unavailable"""
        for i, doc in enumerate(passages, 1):
            print(f"\n📜 Passage {i}:")
            source_info = f"Source: {doc.get('source', 'Unknown')}"
            if doc.get('chapter') and doc.get('verse'):
                source_info += f" (Chapter {doc['chapter']}, Verse {doc['verse']})"
            print(f"   {source_info}")
            
            # Show a snippet of the text
            text = doc.get('text', '').strip()
            if len(text) > 300:
                text = text[:300] + "..."
            print(f"   Text: {text}")
            
            # Show additional metadata if available
            if doc.get('sanskrit'):
                sanskrit = doc['sanskrit'].strip()
                if len(sanskrit) > 200:
                    sanskrit = sanskrit[:200] + "..."
                print(f"   Sanskrit: {sanskrit}")
            
            if doc.get('translation'):
                translation = doc['translation'].strip()
                if len(translation) > 200:
                    translation = translation[:200] + "..."
                print(f"   Translation: {translation}")
    
    def interactive_mode(self):
        """Run the chatbot in interactive mode"""
        print("\n🤖 Backend Chatbot - Interactive Mode")
        print("="*50)
        print("Commands:")
        print("  ask <question>     - Ask a question")
        print("  verse <ch> <v>     - Get specific verse (e.g., 'verse 1 1')")
        print("  stats              - Show database statistics")
        print("  reload             - Reload database")
        print("  quit/exit          - Exit the chatbot")
        print("="*50)
        
        while True:
            try:
                user_input = input("\n💬 Enter command: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                elif user_input.lower() == 'stats':
                    self.get_database_stats()
                    
                elif user_input.lower() == 'reload':
                    self.initialize_database(force_reload=True)
                    
                elif user_input.lower().startswith('verse '):
                    parts = user_input.split()
                    if len(parts) >= 3:
                        chapter, verse = parts[1], parts[2]
                        self.search_by_verse(chapter, verse)
                    else:
                        print("❌ Usage: verse <chapter> <verse>")
                        
                elif user_input.lower().startswith('ask '):
                    question = user_input[4:].strip()
                    if question:
                        self.answer_question(question)
                    else:
                        print("❌ Please provide a question after 'ask'")
                        
                else:
                    # Treat any other input as a direct question
                    self.answer_question(user_input)
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")
                print(f"❌ An error occurred: {e}")

def main():
    """Main function to run the backend chatbot"""
    parser = argparse.ArgumentParser(description="Backend Chatbot using RAG services")
    parser.add_argument('--init', action='store_true', 
                       help='Initialize database with documents')
    parser.add_argument('--force-reload', action='store_true',
                       help='Force reload database (use with --init)')
    parser.add_argument('--question', '-q', type=str,
                       help='Ask a single question and exit')
    parser.add_argument('--verse', nargs=2, metavar=('CHAPTER', 'VERSE'),
                       help='Get a specific verse and exit')
    parser.add_argument('--stats', action='store_true',
                       help='Show database statistics and exit')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode (default)')
    
    args = parser.parse_args()
    
    # Initialize chatbot
    chatbot = BackendChatbot()
    
    # Initialize database if requested
    if args.init:
        if not chatbot.initialize_database(force_reload=args.force_reload):
            sys.exit(1)
    
    # Handle single operations
    if args.stats:
        chatbot.get_database_stats()
        return
        
    if args.verse:
        chapter, verse = args.verse
        chatbot.search_by_verse(chapter, verse)
        return
        
    if args.question:
        chatbot.answer_question(args.question)
        return
    
    # Check if database is initialized for interactive operations
    try:
        stats = chatbot.rag_service.get_database_stats()
        if stats.get('total_documents', 0) == 0:
            print("⚠️  Database appears empty. Would you like to initialize it? (y/n)")
            if input().lower().startswith('y'):
                if not chatbot.initialize_database():
                    sys.exit(1)
            else:
                print("❌ Cannot proceed without initialized database")
                sys.exit(1)
    except Exception as e:
        print(f"⚠️  Could not check database status: {e}")
        print("Would you like to initialize the database? (y/n)")
        if input().lower().startswith('y'):
            if not chatbot.initialize_database():
                sys.exit(1)
        else:
            print("❌ Cannot proceed without initialized database")
            sys.exit(1)
    
    # Default to interactive mode
    chatbot.interactive_mode()

if __name__ == "__main__":
    main()