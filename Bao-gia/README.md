# 📊 QUOTEFLOW OS — AI Quotation Management System

CRM + CPQ + Quotation Management + AI Copilot cho doanh nghiệp Việt Nam.

> Khách hàng → Báo giá → Phê duyệt → Gửi khách → Đàm phán → Đơn hàng → Doanh thu

---

## 1. Phạm vi đã hoàn thành

### Phase 1 — Nghiệp vụ cốt lõi
- Quản lý Khách hàng, Sản phẩm (CRUD, danh mục, tồn kho)
- Tạo báo giá: auto-numbering `BG-2026-000001`, chi tiết dòng, VAT, chiết khấu
- Workflow phê duyệt 3 cấp: Nhân viên → Trưởng phòng → Giám đốc (tự động chuyển cấp nếu chiết khấu > 10%)
- Versioning: lưu snapshot phiên bản báo giá, xem lịch sử
- Xuất PDF (font Unicode có dấu tiếng Việt) và Excel
- Dashboard CEO/Giám đốc/Trưởng phòng/Nhân viên: KPI, Win Rate, Pipeline, Top KH/SP/NV, dự báo doanh thu
- AI Copilot rule-based (không cần API key) trả lời câu hỏi số liệu theo dữ liệu thật
- Import Excel hàng loạt (sản phẩm): template, validate, preview, import
- ERD đầy đủ 14 bảng (SQLAlchemy ORM, chạy trên SQLite — đổi sang PostgreSQL bằng 1 dòng `DATABASE_URL`)
- Docker + docker-compose

### Phase 2 — Bảo mật & Tích hợp thật
- ✅ **JWT Auth thật**: mật khẩu hash bằng bcrypt, đăng nhập username/password xác thực với DB, token có `exp` (mặc định 8 giờ), decode lại token ở mỗi trang
- ✅ **RBAC middleware ở tầng SERVICE** (`auth/rbac.py`): không chỉ ẩn nút trên UI — nếu một role cố gọi thẳng hàm duyệt vượt quyền (vd. Trưởng phòng gọi hàm duyệt bước Giám đốc), hệ thống raise `PermissionDenied` ngay trong `approval_service.py`, đã test bằng script mô phỏng tấn công bypass UI
- ✅ **Gửi email SMTP thật** (`email_module/email_service.py`): đính kèm PDF báo giá, gửi qua Gmail/Outlook/SMTP riêng, ghi log `email_logs` (Sent/Failed/Simulated), xử lý lỗi kết nối gracefully không crash app
- ✅ **Rate-limit chống brute-force** (`auth/rate_limit.py`): khóa tạm 15 phút sau 5 lần đăng nhập sai/tài khoản, dùng chính bảng `audit_logs` sẵn có, không cần Redis
- ✅ **Trang đổi mật khẩu**: verify mật khẩu cũ, ràng buộc độ dài tối thiểu, không cho trùng mật khẩu cũ
- ✅ Cấu hình tách biệt qua `.env` (không hardcode secret)

⏳ Chưa có (Phase 3 — cần thêm hạ tầng riêng của công ty):
- Refresh token / đăng xuất tất cả thiết bị
- Gửi Zalo OA / WhatsApp Business API (cần đăng ký tài khoản doanh nghiệp)
- AI Copilot dùng LLM thật (Claude/GPT API) thay vì rule-based
- Thiết kế mẫu báo giá kéo-thả (logo, chữ ký số, con dấu tùy chỉnh)
- CI/CD pipeline, test coverage đầy đủ (pytest), 2FA cho CEO/Giám đốc

---

## 2. Cấu hình bắt buộc trước khi chạy (.env)

Sao chép `.env.example` thành `.env` và điền thông tin thật:

```bash
cp .env.example .env
```

```ini
# JWT — bắt buộc đổi secret khi lên production
JWT_SECRET=change-this-to-a-long-random-secret-in-production
JWT_EXPIRE_MINUTES=480

# SMTP — nếu để trống, hệ thống tự chuyển sang chế độ MÔ PHỎNG (không gửi email thật)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password   # Gmail: tạo App Password tại myaccount.google.com/apppasswords
SMTP_FROM_NAME=QuoteFlow OS
```

> ⚠️ Nếu chưa cấu hình SMTP thật, nút "Gửi email cho khách hàng" vẫn hoạt động nhưng chỉ ghi log ở chế độ **Simulated** — hệ thống báo rõ điều này trên giao diện, không âm thầm giả vờ đã gửi.

---

## 3. Tài khoản đăng nhập demo

| Username | Mật khẩu | Vai trò |
|---|---|---|
| ceo | 123456 | CEO |
| director | 123456 | Giám đốc kinh doanh |
| manager | 123456 | Trưởng phòng kinh doanh |
| sales1 / sales2 | 123456 | Nhân viên kinh doanh |
| accountant | 123456 | Kế toán |
| admin | 123456 | Admin |

> 🔒 **Bắt buộc đổi mật khẩu demo trước khi đưa vào sử dụng thật** — sửa qua `auth.security.hash_password()` và update trực tiếp cột `password_hash` trong bảng `sales_users`, hoặc xây thêm trang "Đổi mật khẩu" ở Phase 3.

---

## 4. Cài đặt trên Windows (local)

```powershell
# 1. Cài Python 3.11+ từ python.org (tick "Add to PATH")

# 2. Giải nén thư mục QUOTEFLOW_OS, mở PowerShell tại đó
cd QUOTEFLOW_OS

# 3. Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Cài thư viện
pip install -r requirements.txt

# 5. Cấu hình .env (xem mục 2)
copy .env.example .env

# 6. Chạy ứng dụng
streamlit run app.py
```

Ứng dụng sẽ tự mở tại `http://localhost:8501`. Lần chạy đầu tiên tự sinh dữ liệu mẫu (khách hàng, sản phẩm, báo giá demo, 7 tài khoản có mật khẩu hash sẵn) để bạn xem ngay dashboard có số liệu.

> ⚠️ Windows không có sẵn font DejaVu Sans. Nếu PDF xuất ra bị mất dấu tiếng Việt, tải font DejaVu Sans (dejavu-fonts.github.io) và copy `DejaVuSans.ttf`, `DejaVuSans-Bold.ttf` vào `C:\Windows\Fonts`, hoặc chỉnh đường dẫn font trong `services/pdf_service.py`.

---

## 5. Triển khai bằng Docker (khuyến nghị cho production)

```bash
docker compose up -d --build
```

Truy cập `http://<IP-server>:8501`. Dữ liệu SQLite và file export được lưu ngoài container qua volume, không mất khi restart. Nhớ mount thêm file `.env` vào container hoặc set biến môi trường qua `docker-compose.yml`.

Muốn đổi sang PostgreSQL cho môi trường nhiều người dùng đồng thời: sửa `DATABASE_URL` trong `database/db.py` thành chuỗi kết nối PostgreSQL, thêm service `postgres` vào `docker-compose.yml`.

---

## 6. Triển khai Cloud (Streamlit Community Cloud / VPS)

**Cách nhanh nhất — Streamlit Community Cloud (miễn phí, phù hợp demo nội bộ):**
1. Đẩy thư mục này lên GitHub repository (⚠️ đảm bảo `.env` nằm trong `.gitignore`, KHÔNG commit secret)
2. Vào https://share.streamlit.io → New app → chọn repo → file chính `app.py`
3. Thêm `JWT_SECRET`, `SMTP_*` vào mục "Secrets" của Streamlit Cloud
4. Deploy (khoảng 2-3 phút)

**Trên VPS (Ubuntu) chạy production dùng Nginx reverse proxy:**
```bash
sudo apt update && sudo apt install -y docker.io docker-compose-plugin nginx
git clone <repo> && cd QUOTEFLOW_OS
cp .env.example .env && nano .env   # điền secret thật
docker compose up -d --build
```
Sau đó cấu hình Nginx reverse proxy trỏ về `127.0.0.1:8501`, thêm SSL bằng Certbot.

---

## 7. Cấu trúc thư mục

```
QUOTEFLOW_OS/
├── app.py                    # Entry point + đăng nhập JWT
├── .env.example               # Template cấu hình (copy thành .env)
├── config/
│   └── settings.py            # Load .env: JWT_SECRET, SMTP_*
├── auth/
│   ├── security.py            # Hash/verify password (bcrypt)
│   ├── jwt_service.py         # Tạo/giải mã JWT
│   ├── auth_service.py        # Logic đăng nhập
│   ├── rbac.py                 # Middleware kiểm tra quyền theo role
│   └── session.py              # Helper lấy user hiện tại từ token (dùng ở mọi trang)
├── email_module/
│   └── email_service.py       # Gửi email SMTP thật, đính kèm PDF
├── database/
│   ├── db.py                  # Kết nối DB (SQLite/PostgreSQL)
│   └── seed.py                 # Dữ liệu mẫu (kèm mật khẩu hash)
├── models/models.py           # 14 bảng ORM (ERD đầy đủ)
├── services/
│   ├── quotation_service.py   # Tạo báo giá, auto-numbering, versioning
│   ├── approval_service.py    # Workflow phê duyệt 3 cấp + RBAC check
│   ├── kpi_service.py         # Tính KPI, pipeline, forecast
│   ├── pdf_service.py         # Xuất PDF (font Unicode)
│   ├── excel_service.py       # Import/Export Excel
│   └── copilot_service.py     # AI Copilot rule-based
├── pages/                     # 7 trang Streamlit
├── exports/                   # File PDF/Excel xuất ra
├── uploads/                   # File Excel import
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 8. Kiểm thử bảo mật đã thực hiện

Trước khi bàn giao, đã chạy script test mô phỏng tấn công thật (không chỉ test happy-path):
- Đăng nhập sai mật khẩu → bị từ chối, ghi `audit_logs`
- Token giả mạo/sai chữ ký → decode trả về `None`, buộc đăng nhập lại
- **Trưởng phòng cố tình gọi thẳng hàm duyệt bước Giám đốc (bypass UI)** → bị chặn bởi `PermissionDenied` ngay trong tầng service, không phụ thuộc giao diện
- SMTP chưa cấu hình → tự chuyển chế độ mô phỏng, báo rõ cho người dùng, không giả vờ đã gửi
- SMTP cấu hình nhưng server không tồn tại → bắt lỗi gracefully, ghi log "Failed", không crash ứng dụng

