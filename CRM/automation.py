import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from config import Config, Tables
import db
import auth

def send_email_smtp(to_email: str, subject: str, body: str):
    smtp_server = os.environ.get("SMTP_SERVER", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    
    if not (smtp_server and smtp_user and smtp_pass):
        # Nếu không cấu hình SMTP, ghi log lại ra console để dev kiểm tra dễ dàng
        print(f"[MOCK EMAIL] Gửi tới: {to_email}\nTiêu đề: {subject}\nNội dung:\n{body}\n[MOCK EMAIL END]")
        return
        
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = to_email
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_email], msg.as_string())
        server.quit()
        print(f"[EMAIL] Sent successfully to: {to_email}")
    except Exception as e:
        print(f"[EMAIL] Send email failed: {e}")

def trigger_email_workflow(customer_id: str, event_str: str):
    # event_str có dạng "status:Lead" hoặc "status:Đã chốt"
    tpls = db.read_all(Tables.TEMPLATES)
    active = [t for t in tpls if t["active"] == "yes" and t["trigger"] == event_str]
    if not active:
        return
        
    c = db.find_by_id(Tables.CUSTOMERS, customer_id)
    if not c or not c.get("email"):
        return
        
    for t in active:
        subject = t["subject"]
        body = t["body"]
        
        # Thay thế placeholder {{name}}, {{phone}}, {{email}}, {{status}}
        placeholders = {
            "name": c.get("name", ""),
            "phone": c.get("phone", ""),
            "email": c.get("email", ""),
            "status": c.get("status", "")
        }
        for k, v in placeholders.items():
            subject = subject.replace(f"{{{{{k}}}}}", str(v))
            body = body.replace(f"{{{{{k}}}}}", str(v))
            
        try:
            send_email_smtp(c["email"], subject, body)
            db.insert(Tables.AUDIT, {
                "id": auth.gen_id("LOG"),
                "timestamp": datetime.now().isoformat(),
                "user": "system",
                "action": "send_email",
                "target": "customer",
                "targetId": customer_id,
                "detail": f"Gửi email qua template {t['name']} tới {c['email']}"
            })
        except Exception as e:
            print(f"Trigger email workflow error: {e}")

def check_follow_ups_due():
    # Quét các follow up đến hạn
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    followups = db.read_all(Tables.FOLLOWUPS)
    # Lọc các followup ở trạng thái 'pending' và đến hạn
    due = [f for f in followups if f["status"] == "pending" and f["dueDate"] <= today_str and not f.get("remindedAt")]
    
    for f in due:
        c = db.find_by_id(Tables.CUSTOMERS, f["customerId"])
        if not c:
            continue
            
        subject = f"[NEXUS CRM] Nhắc việc chăm sóc khách hàng: {c['name']}"
        body = (
            f"Xin chào,\n\nBạn có lịch hẹn chăm sóc khách hàng sau:\n"
            f"- Khách hàng: {c['name']} ({c['phone'] or 'Không có SĐT'})\n"
            f"- Trạng thái khách hàng: {c['status']}\n"
            f"- Nội dung cuộc hẹn: {f['content']}\n"
            f"- Thời gian hẹn: {f['dueDate']} lúc {f['dueTime'] or 'trong ngày'}\n\n"
            f"Vui lòng truy cập hệ thống để thực hiện."
        )
        
        assigned_email = f["assignedTo"] or c["assignedTo"]
        if assigned_email:
            send_email_smtp(assigned_email, subject, body)
            db.update_by_id(Tables.FOLLOWUPS, f["id"], {"remindedAt": now.isoformat()})
            print(f"[FOLLOWUP REMINDER] Sent reminder for appointment {f['id']} to {assigned_email}")

def scan_gmail_leads() -> int:
    # Quét thư từ nhãn Gmail (Stub/Placeholder cho phiên bản Python cục bộ)
    # Trong môi trường production, có thể sử dụng thư viện imaplib để quét hộp thư Gmail thực tế.
    print("[INTEGRATION] Automatic email scan: IMAP connection not configured.")
    return 0

def api_scan_gmail_manual(token: str) -> dict:
    try:
        auth.guard(token, "admin.users")
        count = scan_gmail_leads()
        return {"ok": True, "data": count}
    except Exception as e:
        return {"ok": False, "error": str(e)}
