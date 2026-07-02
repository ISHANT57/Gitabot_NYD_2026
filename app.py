import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging (INFO in production; set LOG_LEVEL=DEBUG locally for verbose output).
# Note: DEBUG makes urllib3 log full request URLs, which include the Gemini ?key= — avoid in prod.
_log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, _log_level, logging.INFO))

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Import and register blueprints
from routes.main import main_bp
app.register_blueprint(main_bp)

if __name__ == '__main__':
    debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    port = int(os.environ.get("PORT", "5000"))
    app.run(host='0.0.0.0', port=port, debug=debug)
