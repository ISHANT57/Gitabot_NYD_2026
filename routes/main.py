from flask import Blueprint, request, jsonify, render_template
import logging
from services.rag_service import RAGService

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

# Initialize RAG service
rag_service = RAGService()

@main_bp.route('/')
def index():
    """Serve the main web app"""
    return render_template('index.html')

@main_bp.route('/.well-known/appspecific/com.chrome.devtools.json')
def chrome_devtools_probe():
    """Chrome DevTools auto-probes this path; return empty 204 to avoid a noisy 404."""
    return ('', 204)

@main_bp.route('/api/search', methods=['POST'])
def api_search():
    """API endpoint for searching and answering questions"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        source_filter = data.get('source_filter')
        
        if not question:
            return jsonify({
                'error': 'Question is required'
            }), 400
        
        # Map broad filter labels to actual source keys in the DB
        source_map = {
            'gita':         ['bhagavad_gita_qa', 'processed_gita'],
            'ramayana':     ['ramayana_verses_comprehensive', 'ramayana_iyd_dataset', 'ramayana_characters'],
            'mahabharata':  ['mahabharata_characters'],
            # Direct keys also accepted
            'bhagavad_gita_qa':             ['bhagavad_gita_qa'],
            'ramayana_verses_comprehensive': ['ramayana_verses_comprehensive', 'ramayana_iyd_dataset', 'ramayana_characters'],
            'mahabharata_characters':        ['mahabharata_characters'],
        }
        resolved_filter = source_map.get(source_filter, [source_filter] if source_filter else None)

        # Perform search and generate answer
        result = rag_service.search_and_answer(question, resolved_filter)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in API search: {e}")
        return jsonify({
            'error': 'An error occurred while processing your request'
        }), 500

@main_bp.route('/api/verse/<chapter>/<verse>')
def api_get_verse(chapter, verse):
    """API endpoint to get a specific verse"""
    try:
        result = rag_service.search_by_verse(chapter, verse)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting verse {chapter}.{verse}: {e}")
        return jsonify({
            'error': 'An error occurred while retrieving the verse'
        }), 500

@main_bp.route('/api/stats')
def api_stats():
    """API endpoint to get database statistics"""
    try:
        stats = rag_service.get_database_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'error': 'An error occurred while retrieving statistics'
        }), 500

@main_bp.route('/api/initialize', methods=['POST'])
def api_initialize():
    """API endpoint to initialize the database"""
    try:
        data = request.get_json() or {}
        force_reload = data.get('force_reload', False)
        
        rag_service.initialize_database(force_reload=force_reload)
        
        return jsonify({
            'message': 'Database initialized successfully'
        })
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return jsonify({
            'error': 'An error occurred while initializing the database'
        }), 500
