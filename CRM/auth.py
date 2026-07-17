import hashlib
import uuid
import time
import random
from datetime import datetime, timedelta
from config import Config, Tables, PERMISSIONS, Roles
import db

def gen_salt() -> str:
    return str(uuid.uuid4()).replace("-", "")

def hash_password(password: str, salt: str) -> str:
    message = f"{password}:{salt}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()

def base36encode(number: int) -> str:
    if number < 0:
        return ""
    alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
    base36 = ""
    while number:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36 or alphabet[0]

def gen_id(prefix: str = "ID") -> str:
    # Sinh ID khớp với định dạng: prefix + timestamp base36 + random base36
    timestamp = base36encode(int(time.time() * 1000))
    rand_val = random.randint(100000, 99999999)
    rand_part = base36encode(rand_val)[:5]
    return f"{prefix}_{timestamp}_{rand_part}"

def create_session(user: dict) -> str:
    # Tạo session token ngẫu nhiên
    token = hashlib.sha256(str(uuid.uuid4()).encode("utf-8")).hexdigest()[:40]
    now = datetime.now()
    expires = now + timedelta(minutes=Config.SESSION_DURATION_MIN)
    
    session_data = {
        "token": token,
        "email": user["email"],
        "role": user["role"],
        "name": user["name"],
        "createdAt": now.isoformat(),
        "expiresAt": expires.isoformat()
    }
    db.insert(Tables.SESSION, session_data)
    return token

def verify_session(token: str) -> dict | None:
    if not token:
        return None
    session = db.find_by_id(Tables.SESSION, token)
    if not session:
        return None
        
    expires_at = datetime.fromisoformat(session["expiresAt"])
    if expires_at < datetime.now():
        db.delete_by_id(Tables.SESSION, token)
        return None
        
    return {
        "email": session["email"],
        "role": session["role"],
        "name": session["name"],
        "token": token
    }

def destroy_session(token: str):
    db.delete_by_id(Tables.SESSION, token)

def clean_expired_sessions():
    now = datetime.now()
    sessions = db.read_all(Tables.SESSION)
    for s in sessions:
        exp = datetime.fromisoformat(s["expiresAt"])
        if exp < now:
            db.delete_by_id(Tables.SESSION, s["token"])

def guard(token: str, permission: str = None) -> dict:
    user = verify_session(token)
    if not user:
        raise Exception("AUTH: Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.")
        
    if not permission:
        return user
        
    perms = PERMISSIONS.get(user["role"], [])
    
    allowed = False
    for p in perms:
        if p == "*":
            allowed = True
            break
        if p == permission:
            allowed = True
            break
        if p.endswith(".*"):
            prefix = p[:-1] # e.g. "customer."
            if permission.startswith(prefix):
                allowed = True
                break
                
    if not allowed:
        raise Exception("AUTH: Bạn không có quyền thực hiện thao tác này.")
        
    return user
