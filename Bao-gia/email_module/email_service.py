import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from config.settings import (
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
    SMTP_FROM_NAME, SMTP_USE_TLS, smtp_is_configured,
)
from models.models import EmailLog


def send_quotation_email(db, header, to_email: str, pdf_path: str, extra_message: str = ""):
    """
    Gửi email báo giá thật qua SMTP kèm PDF đính kèm.
    Nếu chưa cấu hình SMTP (.env), tự động chuyển sang chế độ MÔ PHỎNG (Simulated)
    và vẫn ghi log để không chặn demo — nhưng cảnh báo rõ cho người dùng.
    Trả về (success: bool, message: str).
    """
    subject = f"Báo giá {header.quote_no} từ {SMTP_FROM_NAME}"
    body = (
        f"Kính gửi Quý khách,\n\n"
        f"Chúng tôi xin gửi báo giá số {header.quote_no} ngày "
        f"{header.quote_date.strftime('%d/%m/%Y')}, hiệu lực đến "
        f"{header.valid_until.strftime('%d/%m/%Y') if header.valid_until else ''}.\n\n"
        f"Tổng giá trị báo giá: {header.grand_total:,.0f} đ (đã bao gồm VAT).\n\n"
        f"{extra_message}\n\n"
        f"Chi tiết báo giá được đính kèm trong file PDF.\n\n"
        f"Trân trọng,\n{SMTP_FROM_NAME}"
    )

    if not smtp_is_configured():
        db.add(EmailLog(header_id=header.id, to_email=to_email, subject=subject, status="Simulated"))
        db.commit()
        return False, (
            "⚠️ SMTP chưa được cấu hình trong file `.env` (SMTP_HOST/SMTP_USER/SMTP_PASSWORD). "
            "Hệ thống đã ghi nhận log ở chế độ MÔ PHỎNG, chưa gửi email thật. "
            "Vui lòng cấu hình `.env` theo hướng dẫn trong README để gửi email thật."
        )

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with open(pdf_path, "rb") as f:
            part = MIMEApplication(f.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename=f"{header.quote_no}.pdf")
            msg.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            if SMTP_USE_TLS:
                server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())

        db.add(EmailLog(header_id=header.id, to_email=to_email, subject=subject, status="Sent"))
        db.commit()
        return True, f"✅ Đã gửi email báo giá {header.quote_no} thành công tới {to_email}."

    except Exception as e:
        db.add(EmailLog(header_id=header.id, to_email=to_email, subject=subject, status="Failed"))
        db.commit()
        return False, f"❌ Gửi email thất bại: {e}"
