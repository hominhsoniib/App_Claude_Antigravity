import bcrypt


def hash_password(plain_password: str) -> str:
    """Hash password bằng thư viện bcrypt thuần (tránh lỗi tương thích của passlib)."""
    # bcrypt nhận vào bytes và trả về bytes
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify mật khẩu thô so với chuỗi hash bcrypt."""
    if not password_hash or not plain_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")
        hash_bytes = password_hash.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False
