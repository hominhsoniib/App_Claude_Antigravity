from database.db import get_session
from models.models import Product, QuotationHeader

db = get_session()
with open("exports/db_inspect.txt", "w", encoding="utf-8") as f:
    f.write("=== RECENT PRODUCTS ===\n")
    for p in db.query(Product).order_by(Product.id.desc()).limit(20).all():
        f.write(f"ID: {p.id} | SKU: {p.sku} | Name: {p.name} | List Price: {p.list_price} | Cost Price: {p.cost_price} | Spec: {p.spec} | Unit: {p.unit} | Category: {p.category}\n")
        
    f.write("\n=== RECENT QUOTATIONS ===\n")
    for q in db.query(QuotationHeader).order_by(QuotationHeader.id.desc()).limit(10).all():
        f.write(f"ID: {q.id} | Quote No: {q.quote_no} | Status: {q.status.value} | Grand Total: {q.grand_total}\n")
        for d in q.details:
            f.write(f"  Line -> Prod ID: {d.product_id} | Qty: {d.qty} | Price: {d.unit_price} | Total: {d.line_total}\n")
            
db.close()
print("Done")
