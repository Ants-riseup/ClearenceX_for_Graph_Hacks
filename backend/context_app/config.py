import os
from pathlib import Path

DATA_ROOT = Path(os.getenv("UPLOAD_ROOT", "uploads")).resolve()
DATA_ROOT.mkdir(parents=True, exist_ok=True)
SECURE_COOKIES = os.getenv("COOKIE_SECURE", "false").lower() == "true"
SESSION_COOKIE = "__Host-clearancex_session" if SECURE_COOKIES else "clearancex_dev_session"
CSRF_COOKIE = "__Host-clearancex_csrf" if SECURE_COOKIES else "clearancex_dev_csrf"
ORIGINS = {x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080").split(",") if x.strip()}
MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_REQUEST_BYTES = 80 * 1024 * 1024
MAX_FILES = 10
MAX_PAGES = 25
