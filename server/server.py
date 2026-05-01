import os
import sys
from . import logger
from flask import Flask, request, make_response, send_from_directory, abort
from werkzeug.middleware.proxy_fix import ProxyFix

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

RESOURCE_PREFIX = "resources"
ADMIN_PREFIX = "admin_pages"
ERROR_TEMPLATE = "error.html"

INDEX_FILE = "LMGGC.html"
ERROR_TEMPLATE = "error.html.jinja"

# --- Flask App Initialization ---
app = Flask(__name__, 
            static_folder=os.path.join(PROJECT_ROOT, "site/public"),
            template_folder=os.path.join(PROJECT_ROOT, ADMIN_PREFIX))
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Ensure log directory exist before the first request
os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)

# --- Route Definitions ---

# Static Files
@app.route('/')
def index():
    return send_from_directory(str(app.static_folder), INDEX_FILE)

@app.route('/<path:filename>')
def serve_public_files(filename):
    return send_from_directory(str(app.static_folder), filename)

# Resources (CSS/JS/Images from PROJECT_ROOT/resources/)
@app.route(f'/{RESOURCE_PREFIX}/<path:filename>')
def serve_resources(filename):
    """Serves files from the project root's resources/ directory."""
    try:
        resource_path = os.path.join(PROJECT_ROOT, RESOURCE_PREFIX)
        return send_from_directory(resource_path, filename)
    except FileNotFoundError:
        abort(404)

# Favicon
@app.route('/favicon.ico')
def favicon():
    return serve_resources('favicon.png')
    
@app.after_request
def log_all_requests(response):
    """Logs details of every request after it has been processed by the app."""
    if response.status_code == 404:
        # logged in errors.log instead (likely bots)
        return response
    try:
        logger.log_flask_request(request, response)
    except Exception as e:
        # Log error but do not crash the request itself
        print(f"CRITICAL: Failed to log request: {e}", file=sys.stderr)
        
    return response

# --- Error Handling ---

# Custom 404 handler
@app.errorhandler(404)
def page_not_found(error):
    logger.log_error_to_file(f"HTTP Error 404 (Not Found): {request.path}")
    try:
        return make_response(app.jinja_env.get_template(ERROR_TEMPLATE).render(
            code=404, message="Not Found"), 404)
    except Exception:
        return make_response("<h1>404 Not Found</h1>", 404)

# Custom 500 handler
@app.errorhandler(500)
def internal_server_error(error):
    logger.log_error_to_file(f"HTTP Error 500 (Internal Server Error): {request.path}")
    try:
        return make_response(app.jinja_env.get_template(ERROR_TEMPLATE).render(
            code=500, message="Internal Server Error"), 500)
    except Exception:
        return make_response("<h1>500 Internal Server Error</h1>", 500)

# --- Main Execution (local) ---

if __name__ == "__main__":
    # Only run locally
    import sys
    try:
        PORT = int(sys.argv[1])
    except (IndexError, ValueError):
        PORT = 1500

    app.run(port=PORT, debug=True)