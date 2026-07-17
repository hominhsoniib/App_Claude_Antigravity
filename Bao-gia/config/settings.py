import os
from dotenv import load_dotenv

load_dotenv()

# --- JWT ---
JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-insecure-secret")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

# --- SMTP ---
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "QuoteFlow OS")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"


def smtp_is_configured():
    """Kiểm tra đã cấu hình SMTP thật hay chưa (chưa cấu hình -> chế độ giả lập)."""
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD and "your-" not in SMTP_USER)
