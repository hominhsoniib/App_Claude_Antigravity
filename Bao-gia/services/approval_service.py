from models.models import ApprovalWorkflow, QuoteStatus, RoleEnum
from services.quotation_service import update_status
from auth.rbac import require_role

DISCOUNT_APPROVAL_THRESHOLD = 10.0  # % chiết khấu > ngưỡng này cần Giám đốc duyệt


def submit_for_approval(db, header_id, actor):
    """Nhân viên kinh doanh gửi báo giá đi duyệt."""
    from models.models import QuotationHeader
    header = db.query(QuotationHeader).get(header_id)
    
    # Luồng phê duyệt 2 cấp: Luôn qua Trưởng phòng duyệt trước (Cấp 1)
    next_status = QuoteStatus.PENDING_MANAGER
    step = "Trưởng phòng duyệt"

    update_status(db, header_id, next_status, actor, "Gửi duyệt")
    db.add(ApprovalWorkflow(header_id=header_id, step=step, approver="-", action="Pending"))
    db.commit()
    return header


def act_on_approval(db, header_id, step, approver, action, current_role: RoleEnum, comment=""):
    """
    action: 'Approved' hoặc 'Rejected'.
    current_role BẮT BUỘC truyền vào để RBAC middleware kiểm tra quyền thật,
    không phụ thuộc vào việc UI có ẩn nút hay không.
    """
    from models.models import QuotationHeader
    header = db.query(QuotationHeader).get(header_id)

    if header.status == QuoteStatus.PENDING_MANAGER:
        require_role(current_role, "approve_manager_step")
    elif header.status == QuoteStatus.PENDING_DIRECTOR:
        require_role(current_role, "approve_director_step")

    db.add(ApprovalWorkflow(header_id=header_id, step=step, approver=approver,
                            action=action, comment=comment))
    db.commit()

    if action == "Rejected":
        update_status(db, header_id, QuoteStatus.REJECTED, approver, comment)
        return header

    # Approved logic
    if header.status == QuoteStatus.PENDING_MANAGER:
        # Trưởng phòng duyệt xong -> có thể cần Giám đốc duyệt tiếp nếu chiết khấu cao
        max_discount = max([d.discount_pct for d in header.details], default=0)
        if max_discount > DISCOUNT_APPROVAL_THRESHOLD:
            update_status(db, header_id, QuoteStatus.PENDING_DIRECTOR, approver, "Chuyển GĐ duyệt")
            db.add(ApprovalWorkflow(header_id=header_id, step="Giám đốc duyệt",
                                    approver="-", action="Pending"))
        else:
            update_status(db, header_id, QuoteStatus.APPROVED, approver, comment)
    elif header.status == QuoteStatus.PENDING_DIRECTOR:
        update_status(db, header_id, QuoteStatus.APPROVED, approver, comment)

    db.commit()
    return header


def mark_sent(db, header_id, actor):
    update_status(db, header_id, QuoteStatus.SENT, actor, "Đã gửi cho khách hàng")


def mark_negotiating(db, header_id, actor):
    update_status(db, header_id, QuoteStatus.NEGOTIATING, actor, "Đang đàm phán với khách hàng")


def mark_won(db, header_id, actor):
    from models.models import QuotationHeader, QuoteStatus
    from services.inventory_service import deduct_stock_from_won_quotation
    
    header = db.query(QuotationHeader).get(header_id)
    if header and header.status != QuoteStatus.WON:
        deduct_stock_from_won_quotation(db, header_id, actor)
        sync_quote_win_to_crm(header, actor)
        
    update_status(db, header_id, QuoteStatus.WON, actor, "Khách hàng đồng ý - Chốt đơn hàng")


def mark_lost(db, header_id, actor, reason=""):
    update_status(db, header_id, QuoteStatus.LOST, actor, f"Mất đơn: {reason}")


def sync_quote_win_to_crm(header, actor):
    import sqlite3
    import os
    from datetime import datetime
    import random
    import time
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crm_db_path = os.path.abspath(os.path.join(base_dir, "..", "CRM-Python", "nexus_crm.db"))
    
    if not os.path.exists(crm_db_path):
        crm_db_path = os.path.abspath(os.path.join(base_dir, "NEXUS-CRM", "CRM-Python", "nexus_crm.db"))
        if not os.path.exists(crm_db_path):
            return
            
    conn = sqlite3.connect(crm_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        crm_cust_id = header.customer.code if header.customer else None
        if not crm_cust_id or not crm_cust_id.startswith("CUST_"):
            return
            
        now_iso = datetime.now().isoformat()
        
        # 1. Tìm Deal chưa chốt của khách hàng này
        cursor.execute(
            "SELECT id, title, value FROM deals WHERE customerId = ? AND stage NOT IN ('Won', 'Lost')",
            (crm_cust_id,)
        )
        deal = cursor.fetchone()
        
        def base36encode(number):
            alphabet = "0123456789abcdefghijklmnopqrstuvwxyz"
            base36 = ""
            while number:
                number, i = divmod(number, 36)
                base36 = alphabet[i] + base36
            return base36 or alphabet[0]
            
        def gen_id(prefix):
            timestamp = base36encode(int(time.time() * 1000))
            rand_val = random.randint(100000, 99999999)
            rand_part = base36encode(rand_val)[:5]
            return f"{prefix}_{timestamp}_{rand_part}"
            
        if deal:
            deal_id = deal["id"]
            cursor.execute(
                "UPDATE deals SET stage = 'Won', wonAt = ?, updatedAt = ? WHERE id = ?",
                (now_iso, now_iso, deal_id)
            )
            detail = f"Cập nhật Deal '{deal['title']}' thành Won từ Báo giá {header.quote_no}."
        else:
            deal_id = gen_id("DEL")
            cursor.execute(
                "INSERT INTO deals (id, customerId, title, value, stage, source, assignedTo, expectedClose, wonAt, createdAt, updatedAt) "
                "VALUES (?, ?, ?, ?, 'Won', 'Website', ?, ?, ?, ?, ?)",
                (deal_id, crm_cust_id, f"Cơ hội từ Báo giá {header.quote_no}", header.grand_total, actor, now_iso, now_iso, now_iso, now_iso)
            )
            detail = f"Tạo Deal mới '{deal_id}' ở trạng thái Won từ Báo giá {header.quote_no}."
            
        # 2. Cập nhật trạng thái khách hàng thành "Đã chốt"
        cursor.execute(
            "UPDATE customers SET status = 'Đã chốt', updatedAt = ? WHERE id = ?",
            (now_iso, crm_cust_id)
        )
        
        # 3. Thêm nhật ký Audit Log vào CRM
        audit_id = gen_id("AUD")
        cursor.execute(
            "INSERT INTO audit_log (id, timestamp, user, action, target, targetId, detail) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (audit_id, now_iso, actor, "DEAL_WON", "deals", deal_id, detail)
        )
        
        conn.commit()
    except Exception as e:
        print(f"[SYNC ERROR] Failed to update CRM deal: {e}")
    finally:
        conn.close()
