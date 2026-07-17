import os
from dotenv import load_dotenv

# Nap cau hinh tu .env cua phan he Bao-gia de dung chung
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, "Bao-gia", ".env")
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

class Config:
    APP_NAME = "NEXUS CRM"
    VERSION = "1.0.0"
    
    # SQLite Database file name
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "nexus_crm.db")
    
    # Session duration
    SESSION_DURATION_MIN = 480  # 8 hours
    TOKEN_BYTES = 24
    
    # Cache
    CACHE_TTL = 300  # 5 minutes
    
    # Backup
    BACKUP_KEEP = 10
    BACKUP_FOLDER_NAME = "NEXUS_CRM_Backups"
    
    # Default Admin account
    DEFAULT_ADMIN_EMAIL = "admin@nexuscrm.com"
    DEFAULT_ADMIN_PASS = "Admin@123"
    DEFAULT_ADMIN_NAME = "Administrator"
    
    # Directory to store uploaded attachments
    UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

# Sheet equivalent table names
class Tables:
    USERS = "users"
    CUSTOMERS = "customers"
    DEALS = "deals"
    CARE = "care_history"
    NOTES = "notes"
    FOLLOWUPS = "follow_ups"
    AUDIT = "audit_log"
    CONFIG = "config"
    SESSION = "sessions"
    TEMPLATES = "email_templates"
    CHANNELS = "channels"
    AILOG = "ai_log"

# Column definitions (Schemas)
SCHEMA = {
    Tables.USERS: ["id", "email", "passwordHash", "salt", "name", "role", "status", "createdAt", "lastLogin"],
    Tables.CUSTOMERS: ["id", "name", "phone", "email", "source", "status", "tags", "assignedTo", "createdAt", "updatedAt", "score", "attachments", "channel", "channelId"],
    Tables.DEALS: ["id", "customerId", "title", "value", "stage", "source", "assignedTo", "expectedClose", "wonAt", "createdAt", "updatedAt"],
    Tables.CARE: ["id", "customerId", "date", "handler", "content", "note", "result", "createdAt"],
    Tables.NOTES: ["id", "customerId", "content", "author", "createdAt"],
    Tables.FOLLOWUPS: ["id", "customerId", "dueDate", "dueTime", "content", "status", "assignedTo", "createdAt", "calendarEventId", "remindedAt"],
    Tables.AUDIT: ["id", "timestamp", "user", "action", "target", "targetId", "detail"],
    Tables.CONFIG: ["key", "value"],
    Tables.SESSION: ["token", "email", "role", "name", "createdAt", "expiresAt"],
    Tables.TEMPLATES: ["id", "name", "trigger", "subject", "body", "active", "createdAt"],
    Tables.CHANNELS: ["id", "channel", "direction", "externalId", "customerId", "payload", "createdAt"],
    Tables.AILOG: ["id", "customerId", "feature", "model", "prompt", "result", "user", "createdAt"]
}

# Roles & Permissions
class Roles:
    ADMIN = "Admin"
    MANAGER = "Manager"
    SALE = "Sale"

PERMISSIONS = {
    Roles.ADMIN: ["*"],
    Roles.MANAGER: [
        "customer.*", "deal.*", "care.*", "note.*", "report.view", 
        "dashboard.view", "ai.*", "followup.*", "file.*", "template.view"
    ],
    Roles.SALE: [
        "customer.view", "customer.create", "customer.update", "deal.*", 
        "care.*", "note.*", "dashboard.view", "ai.*", "followup.*", "file.*"
    ]
}

# Options dropdown
OPTIONS = {
    "SOURCES": ["Facebook", "Zalo", "Website", "Email", "Referral", "Ads"],
    "STATUSES": ["Lead", "Tiềm năng", "Đang tư vấn", "Đàm phán", "Đã chốt", "Thất bại"],
    "STAGES": ["Lead", "Contacted", "Proposal", "Negotiation", "Won", "Lost"],
    "WON_STAGE": "Won",
    "LOST_STAGE": "Lost"
}

# AI Configuration
AI_CONFIG = {
    "PROVIDER": "claude",
    "CLAUDE_MODEL": "claude-sonnet-4-6",
    "OPENAI_MODEL": "gpt-4o",
    "CLAUDE_URL": "https://api.anthropic.com/v1/messages",
    "OPENAI_URL": "https://api.openai.com/v1/chat/completions",
    "MAX_TOKENS": 1024
}

