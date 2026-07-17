from datetime import datetime
from models.models import Product, InventoryTransaction, QuotationHeader, QuoteStatus

def add_transaction(db, product_id, transaction_type, qty, reference_no, note, actor):
    """
    Thêm giao dịch kho, cập nhật số lượng tồn kho sản phẩm.
    transaction_type: 'IMPORT' (Nhập kho), 'EXPORT' (Xuất kho), 'ADJUST' (Điều chỉnh)
    qty: Số lượng giao dịch (luôn >= 0)
    """
    product = db.query(Product).get(product_id)
    if not product:
        raise ValueError(f"Sản phẩm với ID {product_id} không tồn tại.")

    if qty < 0:
        raise ValueError("Số lượng giao dịch không được là số âm.")

    old_qty = product.stock_qty or 0.0
    
    if transaction_type == "IMPORT":
        product.stock_qty = old_qty + qty
        change_qty = qty
    elif transaction_type == "EXPORT":
        product.stock_qty = old_qty - qty
        change_qty = -qty
    elif transaction_type in ("ADJUST", "OPENING"):
        product.stock_qty = qty
        change_qty = qty - old_qty
    else:
        raise ValueError(f"Loại giao dịch {transaction_type} không hợp lệ.")

    # Tạo ghi chú tự động mô tả sự thay đổi tồn kho nếu chưa có ghi chú
    if not note:
        note = f"Thay đổi: {change_qty:+.1f} ({old_qty:.1f} -> {product.stock_qty:.1f})"

    transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type=transaction_type,
        qty=qty,
        reference_no=reference_no,
        note=note,
        created_by=actor,
        created_at=datetime.utcnow()
    )
    
    db.add(transaction)
    db.commit()
    return transaction


def deduct_stock_from_won_quotation(db, header_id, actor):
    """
    Tự động trừ tồn kho tất cả sản phẩm trong báo giá khi chốt sale thành công (QuoteStatus.WON).
    """
    header = db.query(QuotationHeader).get(header_id)
    if not header:
        return False
        
    for detail in header.details:
        if detail.product_id:
            note = f"Xuất kho tự động khi chốt sale báo giá {header.quote_no}"
            add_transaction(
                db=db,
                product_id=detail.product_id,
                transaction_type="EXPORT",
                qty=detail.qty,
                reference_no=header.quote_no,
                note=note,
                actor=actor
            )
    return True
