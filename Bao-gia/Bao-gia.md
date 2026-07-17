# PROMPT CHO CLAUDE CODE

# XÂY DỰNG ỨNG DỤNG PYTHON QUẢN LÝ BÁO GIÁ KHÁCH HÀNG

# QUOTEFLOW OS – AI QUOTATION MANAGEMENT SYSTEM

Bạn là **Enterprise Solution Architect + Sales Director + Senior Python Developer + Chuyên gia CRM & CPQ (Configure Price Quote)**.

Hãy thiết kế và xây dựng một ứng dụng Python hiện đại quản lý báo giá khách hàng từ khâu tạo báo giá đến phê duyệt và theo dõi chuyển đổi thành đơn hàng.

Tên sản phẩm:

# QUOTEFLOW OS

### AI Quotation Management System

Mục tiêu:

Giúp doanh nghiệp chuẩn hóa quy trình báo giá, giảm thời gian lập báo giá, kiểm soát giá bán và nâng cao tỷ lệ chốt đơn.

---

# I. CÔNG NGHỆ

Sử dụng:

Python

Streamlit

DuckDB

SQLite

PostgreSQL

Pandas

Plotly

OpenPyXL

SQLAlchemy

FastAPI

Pydantic

JWT

RBAC

Docker

Pytest

Alembic

---

# II. CHỨC NĂNG CHÍNH

### Quản lý khách hàng

Khách hàng

Liên hệ

Mã số thuế

Địa chỉ

Nhóm khách hàng

Khu vực

Nhân viên phụ trách

Lịch sử giao dịch

Công nợ

Doanh số

---

### Quản lý sản phẩm

Mã hàng

Tên hàng

Quy cách

Đơn vị tính

Giá vốn

Giá bán

Chiết khấu tối đa

VAT

Nhóm hàng

Kho

Tồn kho

---

### Tạo báo giá

Sinh số báo giá tự động:

```text
BG-2026-000001
```

Thông tin:

Khách hàng

Người liên hệ

Ngày báo giá

Hiệu lực báo giá

Điều kiện thanh toán

Điều kiện giao hàng

Thời gian giao hàng

Ghi chú

---

### Chi tiết báo giá

Sản phẩm

Số lượng

Đơn giá

Chiết khấu

VAT

Thành tiền

Tổng cộng

Chi phí vận chuyển

Chi phí khác

---

### Chính sách giá

Giá chuẩn

Giá đại lý

Giá dự án

Giá VIP

Giá xuất khẩu

Giá khuyến mãi

Bảng giá theo khách hàng

Bảng giá theo khu vực

Bảng giá theo thời gian

---

# III. PHÊ DUYỆT BÁO GIÁ

Workflow:

```text
Nhân viên kinh doanh

↓

Tạo báo giá

↓

Trưởng phòng duyệt

↓

Giám đốc duyệt

↓

Gửi khách hàng

↓

Khách hàng phản hồi

↓

Đàm phán

↓

Chốt đơn hàng

↓

Tạo hợp đồng

↓

Tạo đơn bán hàng
```

---

# IV. GỬI BÁO GIÁ

Hỗ trợ:

Email SMTP

PDF

Excel

Zalo

WhatsApp

Link Online

QR Code

---

# V. QUẢN LÝ PHIÊN BẢN

Version 1

Version 2

Version 3

Theo dõi:

Ai sửa

Khi nào sửa

Nội dung sửa

So sánh phiên bản

Khôi phục phiên bản

---

# VI. KPI BÁO GIÁ

Số báo giá

Giá trị báo giá

Tỷ lệ chuyển đổi

Doanh thu tiềm năng

Win Rate

Lost Rate

Thời gian chốt đơn

Top khách hàng

Top nhân viên

Top sản phẩm

---

# VII. DASHBOARD

Dashboard CEO

Dashboard Sales Director

Dashboard Salesman

Hiển thị:

Tổng số báo giá

Tổng giá trị

Tỷ lệ thắng

Doanh thu dự kiến

Top khách hàng

Top sản phẩm

Top nhân viên

Pipeline

Forecast doanh thu

---

# VIII. AI COPILOT

Người dùng có thể hỏi:

```text
Khách hàng nào có tỷ lệ chốt cao nhất?

Báo giá nào quá hạn?

Top sản phẩm bán chạy?

Nhân viên nào có win rate tốt nhất?

Dự báo doanh thu tháng tới.

Đề xuất mức chiết khấu phù hợp.
```

AI trả lời:

Biểu đồ

Bảng số liệu

Phân tích

Khuyến nghị

---

# IX. IMPORT EXCEL

Hỗ trợ:

Upload Excel

Download Template

Kiểm tra dữ liệu

Preview dữ liệu

Import hàng loạt

Rollback Import

---

# X. MẪU BÁO GIÁ

Cho phép thiết kế mẫu:

Logo công ty

Thông tin công ty

Chữ ký số

Con dấu

Điều khoản thương mại

Điều khoản thanh toán

Điều khoản bảo hành

---

Xuất:

PDF

Excel

Word

---

# XI. DATABASE

Thiết kế ERD hoàn chỉnh.

Các bảng:

```text
customers

contacts

products

price_lists

quotation_header

quotation_detail

quotation_versions

quotation_status

approval_workflow

sales_users

discount_policy

attachments

email_logs

audit_logs
```

---

# XII. PHÂN QUYỀN

CEO

Giám đốc kinh doanh

Trưởng phòng kinh doanh

Nhân viên kinh doanh

Kế toán

Admin

Viewer

---

# XIII. KIẾN TRÚC THƯ MỤC

```text
QUOTEFLOW_OS/

app.py

config/

database/

models/

repositories/

services/

dashboard/

reports/

templates/

auth/

workflow/

exports/

uploads/

pdf/

email/

tests/

docs/

requirements.txt
```

---

# XIV. GIAO DIỆN

Phong cách:

HubSpot

Salesforce

Zoho CRM

Monday

Power BI

Dark Mode

Responsive

Sidebar

Cards

Widgets

Kanban Pipeline

---

# XV. YÊU CẦU KỸ THUẬT

Áp dụng:

Clean Architecture

DDD

SOLID

Repository Pattern

Service Layer

Dependency Injection

Pydantic

Alembic

Pytest

Docker

CI/CD

Logging

Caching

---

# XVI. KẾT QUẢ ĐẦU RA

Claude cần tạo:

✅ Kiến trúc tổng thể

✅ ERD

✅ Database Schema

✅ Use Case Diagram

✅ Wireframe UI

✅ Dashboard Sales

✅ Dashboard CEO

✅ requirements.txt

✅ Folder Structure

✅ File Excel mẫu

✅ Template PDF báo giá

✅ Source code hoàn chỉnh

✅ Dockerfile

✅ Hướng dẫn cài đặt

✅ Hướng dẫn triển khai trên Windows và Cloud

---

## Định vị sản phẩm

> **QUOTEFLOW OS**
>
> *CRM + CPQ + Quotation Management + AI Copilot*
>
> **Khách hàng → Báo giá → Phê duyệt → Gửi khách → Đàm phán → Đơn hàng → Hợp đồng → Doanh thu**.
