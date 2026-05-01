import datetime
import logging
import logging.handlers
import requests
import os
from urllib.parse import urlparse
from user_agents import parse

# --- Configuration ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
GEO_IP_API = "http://ip-api.com/json/{ip}?fields=country,regionName,city"
LOG_FORMAT = "[{timestamp}] [{ip}] [{country}/{region}/{city}] [Referrer: {referrer}] [{method}] {url} | Agent: {user_agent}"

LOG_FILE = os.path.join(PROJECT_ROOT, "logs/requests.log")
ERROR_LOG_FILE = os.path.join(PROJECT_ROOT, "logs/errors.log")
LOG_NUMBER = int(os.getenv("LOG_NUMBER") or 5)
LOG_SIZE = int(os.getenv("LOG_SIZE") or 40 * 1024 * 1024)
ERROR_LOG_NUMBER = int(os.getenv("ERROR_LOG_NUMBER") or 3)
ERROR_LOG_SIZE = int(os.getenv("ERROR_LOG_SIZE") or 40 * 1024 * 1024)

STATIC_ASSET_EXTENSIONS = (
    '.css', '.js', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
    '.woff', '.woff2', '.ttf', '.otf', '.eot', '.map', '.json', '.txt'
)


def _make_rotating_logger(name, log_file, max_bytes, backup_count):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, delay=True
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


_request_logger = _make_rotating_logger("staticserver.requests", LOG_FILE, LOG_SIZE, LOG_NUMBER)
_error_logger = _make_rotating_logger("staticserver.errors", ERROR_LOG_FILE, ERROR_LOG_SIZE, ERROR_LOG_NUMBER)


def log_error_to_file(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _error_logger.error(f"[{timestamp}] {message}")


def is_static_asset(url_path):
    path = urlparse(url_path).path
    return path.lower().endswith(STATIC_ASSET_EXTENSIONS)


def is_bot(user_agent_string):
    if not user_agent_string:
        return False
    user_agent = parse(user_agent_string)
    return user_agent.is_bot


def get_geolocation(ip_address):
    """
    Attempts to get location data for a given IP address.
    NOTE: Currently rate limited to 45/min, do batch lookup to increase
    """
    if ip_address in ('127.0.0.1', 'localhost'):
        return "N/A", "N/A", "N/A"

    try:
        response = requests.get(GEO_IP_API.format(ip=ip_address), timeout=0.5)
        response.raise_for_status()
        data = response.json()

        country = data.get('country', 'Unknown')
        region = data.get('regionName', 'Unknown')
        city = data.get('city', 'Unknown')

        return country, region, city

    except requests.RequestException as e:
        log_error_to_file(f"GeoIP failed for {ip_address}: {e}")
        return "GeoIP-Failed", "GeoIP-Failed", "GeoIP-Failed"


def log_flask_request(request, response):
    """Logs the details of the incoming Flask HTTP request to the LOG_FILE."""
    method = request.method
    url = request.full_path
    referrer = request.headers.get('Referer', 'N/A')
    user_agent = request.headers.get('User-Agent', 'N/A')

    ip = request.remote_addr or "Unknown IP"

    if is_static_asset(url) or is_bot(user_agent):
        return

    country, region, city = get_geolocation(ip)

    log_entry = LOG_FORMAT.format(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ip=ip,
        country=country,
        region=region,
        city=city,
        referrer=referrer,
        method=method,
        url=url,
        user_agent=user_agent
    )

    _request_logger.info(log_entry)
