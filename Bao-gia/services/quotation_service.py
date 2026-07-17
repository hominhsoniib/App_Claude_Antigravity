import json
from datetime import datetime, timedelta
from models.models import (
    QuotationHeader, QuotationDetail, QuotationVersion, QuoteStatus, AuditLog
)


def generate_quote_no(db):
    """Sinh số báo giá tự động dạng BG-YYYY-000001"""
    year = datetime.utcnow().year
    prefix = f"BG-{year}-"
    last = (
        db.query(QuotationHeader)
        .filter(QuotationHeader.quote_no.like(f"{prefix}%"))
        .order_by(QuotationHeader.id.desc())
        .first()
    )
    if last:
        last_seq = int(last.quote_no.split("-")[-1])
        seq = last_seq + 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


def create_quotation(db, customer_id, sales_rep_id, contact_id=None, valid_days=15,
                      payment_terms="", delivery_terms="", lead_time="", note="",
                      shipping_fee=0, other_fee=0, actor="system"):
    header = QuotationHeader(
        quote_no=generate_quote_no(db),
        customer_id=customer_id,
        contact_id=contact_id,
        sales_rep_id=sales_rep_id,
        quote_date=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(days=valid_days),
        payment_terms=payment_terms,
        delivery_terms=delivery_terms,
        lead_time=lead_time,
        note=note,
        shipping_fee=shipping_fee,
        other_fee=other_fee,
        status=QuoteStatus.DRAFT,
        current_version=1,
    )
    db.add(header)
    db.flush()
    _log(db, "quotation_header", header.id, "CREATE", actor, f"Tạo báo giá {header.quote_no}")
    db.commit()
    return header


def add_line(db, header_id, product_id, qty, unit_price, discount_pct=0, vat_pct=10):
    line = QuotationDetail(
        header_id=header_id, product_id=product_id, qty=qty,
        unit_price=unit_price, discount_pct=discount_pct, vat_pct=vat_pct,
    )
    db.add(line)
    db.commit()
    return line


def delete_line(db, line_id):
    line = db.query(QuotationDetail).get(line_id)
    if line:
        db.delete(line)
        db.commit()


def snapshot_version(db, header_id, actor="system", note="Cập nhật báo giá"):
    """Lưu snapshot phiên bản hiện tại trước khi thay đổi lớn."""
    header = db.query(QuotationHeader).get(header_id)
    if not header:
        return None
    data = {
        "quote_no": header.quote_no,
        "status": header.status.value if header.status else None,
        "shipping_fee": header.shipping_fee,
        "other_fee": header.other_fee,
        "lines": [
            {
                "product_id": d.product_id,
                "qty": d.qty,
                "unit_price": d.unit_price,
                "discount_pct": d.discount_pct,
                "vat_pct": d.vat_pct,
            }
            for d in header.details
        ],
        "grand_total": header.grand_total,
    }
    version = QuotationVersion(
        header_id=header_id,
        version_no=header.current_version,
        snapshot_json=json.dumps(data, ensure_ascii=False),
        changed_by=actor,
        change_note=note,
    )
    db.add(version)
    header.current_version += 1
    db.commit()
    return version


def update_status(db, header_id, new_status: QuoteStatus, actor="system", comment=""):
    header = db.query(QuotationHeader).get(header_id)
    if not header:
        return None
    old_status = header.status
    header.status = new_status
    db.commit()
    _log(db, "quotation_header", header_id, "STATUS_CHANGE", actor,
         f"{old_status.value if old_status else '-'} -> {new_status.value} | {comment}")
    return header


def _log(db, entity, entity_id, action, actor, detail):
    db.add(AuditLog(entity=entity, entity_id=entity_id, action=action, actor=actor, detail=detail))
    db.commit()
