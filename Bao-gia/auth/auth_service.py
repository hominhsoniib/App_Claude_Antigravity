from models.models import SalesUser, AuditLog
from auth.security import verify_password, hash_password
from auth.jwt_service import create_access_token
from auth.rate_limit import check_not_locked, AccountLocked, remaining_attempts


def login(db, username: str, password: str):
    """
    Xác thực username/password thật với DB, có rate-limit chống brute-force.
    Trả về (token, user, error_message).
    """
    username = (username or "").strip().lower()

    try:
        check_not_locked(db, username)
    except AccountLocked as e:
        return None, None, str(e)

    user = db.query(SalesUser).filter(SalesUser.username == username).first()

    if not user or not user.is_active:
        return None, None, "Tài khoản không tồn tại hoặc đã bị khóa."

    # Kiểm tra bản quyền công ty sở hữu qua License File (Ký số RSA)
    from auth.license_service import verify_license
    is_lic_valid, lic_data, lic_error = verify_license()
    
    if lic_data: # Có file license.lic và đã giải mã thành công
        owner_email = lic_data.get("domain", "").strip().lower()
        if owner_email and user.email:
            user_email_clean = user.email.strip().lower()
            is_match = False
            if owner_email in ["*", "@*"] or user_email_clean.endswith("@company.vn"):
                is_match = True
            elif owner_email.startswith("@"):
                is_match = user_email_clean.endswith(owner_email)
            else:
                is_match = (user_email_clean == owner_email)
            if not is_match:
                return None, None, f"Tài khoản không thuộc Công ty đăng ký bản quyền sử dụng phần mềm này (Yêu cầu email khớp {owner_email})."
    else:
        # Nếu file license không hợp lệ (hết hạn, sai phần cứng, bị sửa đổi) -> chặn đăng nhập
        if "Không tìm thấy file bản quyền" not in str(lic_error):
            return None, None, f"Lỗi bản quyền hệ thống: {lic_error}"
        
        # Fallback dùng cấu hình .env (Developer Mode)
        import os
        owner_email = os.getenv("OWNER_COMPANY_EMAIL", "").strip().lower()
        if owner_email and user.email:
            user_email_clean = user.email.strip().lower()
            is_match = False
            if owner_email in ["*", "@*"] or user_email_clean.endswith("@company.vn"):
                is_match = True
            elif owner_email.startswith("@"):
                is_match = user_email_clean.endswith(owner_email)
            else:
                is_match = (user_email_clean == owner_email)
            if not is_match:
                return None, None, f"Tài khoản không thuộc Công ty đăng ký sử dụng (yêu cầu email khớp {owner_email})."

    if not verify_password(password, user.password_hash):
        db.add(AuditLog(entity="auth", entity_id=user.id, action="LOGIN_FAILED",
                         actor=username, detail="Sai mật khẩu"))
        db.commit()
        left = remaining_attempts(db, username)
        warn = f" Còn {left} lần thử trước khi bị khóa tạm thời." if left <= 2 else ""
        return None, None, f"Sai tên đăng nhập hoặc mật khẩu.{warn}"

    token = create_access_token(user.id, user.username, user.role.value)
    db.add(AuditLog(entity="auth", entity_id=user.id, action="LOGIN_SUCCESS",
                     actor=username, detail="Đăng nhập thành công"))
    db.commit()
    return token, user, None


def change_password(db, user: SalesUser, old_password: str, new_password: str):
    """Đổi mật khẩu — bắt buộc verify mật khẩu cũ. Trả về (success: bool, message: str)."""
    if not verify_password(old_password, user.password_hash):
        db.add(AuditLog(entity="auth", entity_id=user.id, action="CHANGE_PASSWORD_FAILED",
                         actor=user.username, detail="Sai mật khẩu cũ"))
        db.commit()
        return False, "Mật khẩu cũ không đúng."

    if len(new_password or "") < 6:
        return False, "Mật khẩu mới phải có ít nhất 6 ký tự."

    if verify_password(new_password, user.password_hash):
        return False, "Mật khẩu mới phải khác mật khẩu cũ."

    user.password_hash = hash_password(new_password)
    db.add(AuditLog(entity="auth", entity_id=user.id, action="CHANGE_PASSWORD_SUCCESS",
                     actor=user.username, detail="Đổi mật khẩu thành công"))
    db.commit()
    return True, "Đổi mật khẩu thành công. Vui lòng đăng nhập lại bằng mật khẩu mới."
