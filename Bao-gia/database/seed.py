"""Seed dữ liệu mẫu cho QUOTEFLOW OS (chạy 1 lần khi DB trống)."""
import random
from datetime import datetime, timedelta
from database.db import get_session, init_db
from models.models import (
    SalesUser, Customer, Contact, Product, DiscountPolicy,
    QuotationHeader, QuotationDetail, ApprovalWorkflow, QuoteStatus, RoleEnum
)
from auth.security import hash_password

DEMO_PASSWORD = "QuoteFlow@2026"  # Mật khẩu demo cho TẤT CẢ tài khoản seed — đổi ngay khi triển khai thật


def seed_if_empty():
    init_db()
    db = get_session()
    try:
        if db.query(SalesUser).count() > 0:
            return  # đã seed rồi

        # --- Sales Users ---
        pwd_hash = hash_password(DEMO_PASSWORD)
        users = [
            SalesUser(username="ceo", password_hash=pwd_hash, full_name="Nguyễn Văn An", role=RoleEnum.CEO, email="ceo@company.vn"),
            SalesUser(username="director", password_hash=pwd_hash, full_name="Trần Thị Bích", role=RoleEnum.SALES_DIRECTOR, email="director@company.vn"),
            SalesUser(username="manager", password_hash=pwd_hash, full_name="Lê Văn Cường", role=RoleEnum.SALES_MANAGER, email="manager@company.vn"),
            SalesUser(username="sales1", password_hash=pwd_hash, full_name="Phạm Thị Dung", role=RoleEnum.SALESMAN, email="dung@company.vn"),
            SalesUser(username="sales2", password_hash=pwd_hash, full_name="Hoàng Văn Em", role=RoleEnum.SALESMAN, email="em@company.vn"),
            SalesUser(username="accountant", password_hash=pwd_hash, full_name="Vũ Thị Phương", role=RoleEnum.ACCOUNTANT, email="ketoan@company.vn"),
            SalesUser(username="admin", password_hash=pwd_hash, full_name="Quản trị hệ thống", role=RoleEnum.ADMIN, email="admin@company.vn"),
        ]
        db.add_all(users)
        db.flush()

        # --- Discount policy ---
        db.add(DiscountPolicy(name="Chính sách chuẩn", max_pct=20, requires_approval_above=10))

        # --- Customers ---
        cust_names = [
            ("Công ty TNHH Xây dựng Phương Nam", "Đại lý", "TP.HCM"),
            ("Công ty CP Vật liệu Miền Trung", "Dự án", "Đà Nẵng"),
            ("Tập đoàn Thép Việt Hưng", "VIP", "Hà Nội"),
            ("Công ty TNHH TM Hoàng Gia", "Đại lý", "Cần Thơ"),
            ("Công ty CP Xuất nhập khẩu Đông Á", "Xuất khẩu", "TP.HCM"),
            ("Công ty TNHH Cơ khí Tân Bình", "Dự án", "TP.HCM"),
            ("Công ty CP Nội thất Gia Phát", "Đại lý", "Bình Dương"),
            ("Công ty TNHH Thiết bị Công nghiệp An Phát", "VIP", "Hà Nội"),
        ]
        customers = []
        for i, (name, grp, region) in enumerate(cust_names, start=1):
            c = Customer(
                code=f"KH{i:04d}", name=name, tax_code=f"03001234{i:02d}",
                address=f"Số {i}, Đường Công Nghiệp, {region}",
                group=grp, region=region,
                sales_rep_id=random.choice([users[3].id, users[4].id]),
                debt=random.randint(0, 200_000_000),
                revenue_ytd=random.randint(100_000_000, 3_000_000_000),
            )
            customers.append(c)
        db.add_all(customers)
        db.flush()

        for c in customers:
            db.add(Contact(customer_id=c.id, name=f"Anh/Chị Đại diện {c.code}",
                            phone="0901234567", email=f"contact.{c.code.lower()}@khachhang.vn",
                            position="Trưởng phòng Mua hàng"))

        # --- Products ---
        prod_data = [
            ("Thép hộp mạ kẽm 50x50x2mm", "Cây 6m", "Cây", 180000, 235000, "Vật liệu thép"),
            ("Tôn lạnh 0.45mm", "Tấm khổ 1.07m", "m2", 65000, 89000, "Tôn - Mái"),
            ("Xi măng PCB40", "Bao 50kg", "Bao", 78000, 95000, "Vật liệu xây dựng"),
            ("Sơn chống rỉ Epoxy", "Thùng 18L", "Thùng", 950000, 1250000, "Hóa chất - Sơn"),
            ("Bulong lục giác M16", "Hộp 100 con", "Hộp", 320000, 420000, "Phụ kiện"),
            ("Máy hàn điện tử Inverter 250A", "Chiếc", "Chiếc", 2800000, 3650000, "Thiết bị công nghiệp"),
            ("Ống thép đúc D114", "Cây 6m", "Cây", 890000, 1150000, "Vật liệu thép"),
            ("Kính cường lực 10mm", "m2", "m2", 450000, 590000, "Vật liệu xây dựng"),
        ]
        products = []
        for i, (name, spec, unit, cost, price, cat) in enumerate(prod_data, start=1):
            p = Product(sku=f"SP{i:04d}", name=name, spec=spec, unit=unit,
                        cost_price=cost, list_price=price, max_discount_pct=15,
                        vat_pct=10, category=cat, warehouse="Kho HCM",
                        stock_qty=random.randint(50, 2000))
            products.append(p)
        db.add_all(products)
        db.flush()

        # --- Quotations mẫu (đa dạng status để dashboard có số liệu) ---
        statuses_pool = [
            QuoteStatus.DRAFT, QuoteStatus.PENDING_MANAGER, QuoteStatus.PENDING_DIRECTOR,
            QuoteStatus.APPROVED, QuoteStatus.SENT, QuoteStatus.NEGOTIATING,
            QuoteStatus.WON, QuoteStatus.WON, QuoteStatus.LOST, QuoteStatus.EXPIRED,
        ]
        quote_counter = 1
        today = datetime.utcnow()
        for i in range(24):
            cust = random.choice(customers)
            rep_id = cust.sales_rep_id
            q_date = today - timedelta(days=random.randint(0, 75))
            status = random.choice(statuses_pool)
            header = QuotationHeader(
                quote_no=f"BG-2026-{quote_counter:06d}",
                customer_id=cust.id,
                sales_rep_id=rep_id,
                quote_date=q_date,
                valid_until=q_date + timedelta(days=15),
                payment_terms="Thanh toán 50% đặt cọc, 50% khi giao hàng",
                delivery_terms="Giao hàng tại kho khách hàng",
                lead_time=f"{random.randint(3,15)} ngày làm việc",
                note="Báo giá theo yêu cầu khách hàng",
                shipping_fee=random.choice([0, 500000, 1200000]),
                other_fee=0,
                status=status,
                current_version=1,
                created_at=q_date,
                updated_at=q_date,
            )
            db.add(header)
            db.flush()

            n_lines = random.randint(2, 5)
            chosen_products = random.sample(products, n_lines)
            for p in chosen_products:
                db.add(QuotationDetail(
                    header_id=header.id, product_id=p.id,
                    qty=random.randint(5, 100),
                    unit_price=p.list_price,
                    discount_pct=random.choice([0, 3, 5, 8, 10]),
                    vat_pct=p.vat_pct,
                ))
            quote_counter += 1

        db.commit()
    finally:
        db.close()
