"""
QUOTEFLOW OS - Data Models
ERD: customers, contacts, products, price_lists, quotation_header,
quotation_detail, quotation_versions, quotation_status, approval_workflow,
sales_users, discount_policy, attachments, email_logs, audit_logs
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Enum
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class RoleEnum(str, enum.Enum):
    CEO = "CEO"
    SALES_DIRECTOR = "Giám đốc kinh doanh"
    SALES_MANAGER = "Trưởng phòng kinh doanh"
    SALESMAN = "Nhân viên kinh doanh"
    ACCOUNTANT = "Kế toán"
    ADMIN = "Admin"
    VIEWER = "Viewer"


class QuoteStatus(str, enum.Enum):
    DRAFT = "Nháp"
    PENDING_MANAGER = "Chờ Trưởng phòng duyệt"
    PENDING_DIRECTOR = "Chờ Giám đốc duyệt"
    APPROVED = "Đã duyệt"
    SENT = "Đã gửi khách"
    NEGOTIATING = "Đang đàm phán"
    WON = "Chốt đơn (Win)"
    LOST = "Mất đơn (Lost)"
    EXPIRED = "Hết hạn"
    REJECTED = "Bị từ chối"


class SalesUser(Base):
    __tablename__ = "sales_users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(200), nullable=True)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    quotations = relationship("QuotationHeader", back_populates="sales_rep")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    code = Column(String(30), unique=True)
    name = Column(String(200), nullable=False)
    tax_code = Column(String(30))
    address = Column(String(300))
    group = Column(String(50))            # Nhóm khách hàng: Đại lý/Dự án/VIP...
    region = Column(String(50))            # Khu vực
    sales_rep_id = Column(Integer, ForeignKey("sales_users.id"))
    debt = Column(Float, default=0)        # Công nợ
    revenue_ytd = Column(Float, default=0) # Doanh số
    created_at = Column(DateTime, default=datetime.utcnow)

    contacts = relationship("Contact", back_populates="customer")
    quotations = relationship("QuotationHeader", back_populates="customer")


class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    name = Column(String(100))
    phone = Column(String(30))
    email = Column(String(100))
    position = Column(String(100))

    customer = relationship("Customer", back_populates="contacts")


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String(30), unique=True)
    name = Column(String(200), nullable=False)
    spec = Column(String(200))             # Quy cách
    unit = Column(String(20))              # ĐVT
    cost_price = Column(Float, default=0)  # Giá vốn
    list_price = Column(Float, default=0)  # Giá bán
    max_discount_pct = Column(Float, default=0)
    vat_pct = Column(Float, default=10)
    category = Column(String(50))          # Nhóm hàng
    warehouse = Column(String(50))
    stock_qty = Column(Float, default=0)


class PriceList(Base):
    __tablename__ = "price_lists"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))             # Giá chuẩn/Đại lý/Dự án/VIP/Xuất khẩu/KM
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    customer_group = Column(String(50), nullable=True)
    region = Column(String(50), nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)


class DiscountPolicy(Base):
    __tablename__ = "discount_policy"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    max_pct = Column(Float)
    requires_approval_above = Column(Float, default=10.0)  # % chiết khấu cần duyệt GĐ


class QuotationHeader(Base):
    __tablename__ = "quotation_header"
    id = Column(Integer, primary_key=True)
    quote_no = Column(String(30), unique=True, nullable=False)  # BG-2026-000001
    customer_id = Column(Integer, ForeignKey("customers.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    sales_rep_id = Column(Integer, ForeignKey("sales_users.id"))
    quote_date = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)
    payment_terms = Column(String(200))
    delivery_terms = Column(String(200))
    lead_time = Column(String(100))
    note = Column(Text)
    shipping_fee = Column(Float, default=0)
    other_fee = Column(Float, default=0)
    status = Column(Enum(QuoteStatus), default=QuoteStatus.DRAFT)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="quotations")
    sales_rep = relationship("SalesUser", back_populates="quotations")
    details = relationship("QuotationDetail", back_populates="header", cascade="all, delete-orphan")
    versions = relationship("QuotationVersion", back_populates="header", cascade="all, delete-orphan")
    approvals = relationship("ApprovalWorkflow", back_populates="header", cascade="all, delete-orphan")

    @property
    def subtotal(self):
        return sum(d.line_total for d in self.details)

    @property
    def vat_total(self):
        return sum(d.line_total * (d.vat_pct / 100) for d in self.details)

    @property
    def grand_total(self):
        return self.subtotal + self.vat_total + (self.shipping_fee or 0) + (self.other_fee or 0)


class QuotationDetail(Base):
    __tablename__ = "quotation_detail"
    id = Column(Integer, primary_key=True)
    header_id = Column(Integer, ForeignKey("quotation_header.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    qty = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    discount_pct = Column(Float, default=0)
    vat_pct = Column(Float, default=10)

    header = relationship("QuotationHeader", back_populates="details")
    product = relationship("Product")

    @property
    def line_total(self):
        return self.qty * self.unit_price * (1 - self.discount_pct / 100)


class QuotationVersion(Base):
    __tablename__ = "quotation_versions"
    id = Column(Integer, primary_key=True)
    header_id = Column(Integer, ForeignKey("quotation_header.id"))
    version_no = Column(Integer)
    snapshot_json = Column(Text)     # JSON snapshot toàn bộ báo giá tại thời điểm đó
    changed_by = Column(String(100))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_note = Column(String(300))

    header = relationship("QuotationHeader", back_populates="versions")


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflow"
    id = Column(Integer, primary_key=True)
    header_id = Column(Integer, ForeignKey("quotation_header.id"))
    step = Column(String(50))         # "Trưởng phòng duyệt" / "Giám đốc duyệt"
    approver = Column(String(100))
    action = Column(String(20))       # Approved / Rejected / Pending
    comment = Column(String(300))
    acted_at = Column(DateTime, default=datetime.utcnow)

    header = relationship("QuotationHeader", back_populates="approvals")


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True)
    header_id = Column(Integer, ForeignKey("quotation_header.id"))
    file_name = Column(String(200))
    file_path = Column(String(300))
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"
    id = Column(Integer, primary_key=True)
    header_id = Column(Integer, ForeignKey("quotation_header.id"))
    to_email = Column(String(100))
    subject = Column(String(200))
    status = Column(String(20))       # Sent / Failed / Simulated
    sent_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    entity = Column(String(50))
    entity_id = Column(Integer)
    action = Column(String(50))
    actor = Column(String(100))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    transaction_type = Column(String(20))  # 'IMPORT' (Nhập kho), 'EXPORT' (Xuất kho), 'ADJUST' (Điều chỉnh)
    qty = Column(Float, nullable=False)     # Số lượng thực hiện
    reference_no = Column(String(50))      # Mã đối chiếu (Mã báo giá, Số phiếu nhập/xuất)
    note = Column(String(300))             # Ghi chú
    created_by = Column(String(100))        # Người thực hiện
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")

