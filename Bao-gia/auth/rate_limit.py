"""
Rate limiting chống brute-force login.
Tận dụng bảng audit_logs đã có (action='LOGIN_FAILED') làm nguồn đếm —
không cần thêm bảng mới, không cần Redis cho quy mô SMB.
"""
from datetime import datetime, timedelta
from models.models import AuditLog

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 15


class AccountLocked(Exception):
    def __init__(self, retry_after_minutes: int):
        self.retry_after_minutes = retry_after_minutes
        super().__init__(
            f"Tài khoản tạm khóa do đăng nhập sai quá {MAX_FAILED_ATTEMPTS} lần. "
            f"Vui lòng thử lại sau khoảng {retry_after_minutes} phút."
        )


def count_recent_failed_attempts(db, username: str) -> int:
    window_start = datetime.utcnow() - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.entity == "auth",
            AuditLog.action == "LOGIN_FAILED",
            AuditLog.actor == username,
            AuditLog.created_at >= window_start,
        )
        .count()
    )


def check_not_locked(db, username: str):
    """Raise AccountLocked nếu tài khoản đang bị khóa tạm thời. Gọi TRƯỚC khi verify password."""
    failed_count = count_recent_failed_attempts(db, username)
    if failed_count >= MAX_FAILED_ATTEMPTS:
        oldest_in_window = (
            db.query(AuditLog)
            .filter(
                AuditLog.entity == "auth",
                AuditLog.action == "LOGIN_FAILED",
                AuditLog.actor == username,
            )
            .order_by(AuditLog.id.desc())
            .limit(MAX_FAILED_ATTEMPTS)
            .all()
        )
        earliest = min(a.created_at for a in oldest_in_window)
        unlock_at = earliest + timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
        retry_after = max(1, int((unlock_at - datetime.utcnow()).total_seconds() // 60) + 1)
        raise AccountLocked(retry_after)


def remaining_attempts(db, username: str) -> int:
    return max(0, MAX_FAILED_ATTEMPTS - count_recent_failed_attempts(db, username))
