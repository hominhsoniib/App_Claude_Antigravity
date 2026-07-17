import streamlit as st
from database.db import get_session
from database.seed import seed_if_empty, DEMO_PASSWORD
from models.models import SalesUser
from auth.auth_service import login
from auth.jwt_service import decode_access_token
from config.settings import smtp_is_configured
from services import kpi_service as kpi

st.set_page_config(page_title="QUOTEFLOW OS", page_icon="📊", layout="wide")

# --- Kiểm tra bản quyền hệ thống trước tiên ---
from auth.license_service import verify_license, show_activation_screen
is_lic_valid, lic_data, lic_error = verify_license()
if not is_lic_valid:
    show_activation_screen(lic_error)

from config.theme import apply_custom_theme
apply_custom_theme()

# --- Khởi tạo database và dữ liệu mẫu một lần duy nhất khi ứng dụng chạy ---
@st.cache_resource
def initialize_database():
    seed_if_empty()

initialize_database()


def show_login():
    st.markdown(
        """
        <div style='text-align:center; padding-top: 40px;'>
            <h1 style='color:#1F3864;'>📊 QUOTEFLOW OS</h1>
            <p style='color:#666;'>AI Quotation Management System — CRM + CPQ + AI Copilot</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.subheader("🔐 Đăng nhập")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submitted = st.form_submit_button("Đăng nhập", use_container_width=True, type="primary")

        if submitted:
            db = get_session()
            try:
                token, user, error = login(db, username, password)
                if error:
                    st.error(error)
                else:
                    st.session_state["token"] = token
                    st.success(f"Xin chào {user.full_name}!")
                    st.rerun()
            finally:
                db.close()

        with st.expander("🧪 Tài khoản demo (dùng để test)"):
            st.code(
                "ceo / director / manager / sales1 / sales2 / accountant / admin\n"
                f"Mật khẩu chung: {DEMO_PASSWORD}",
                language="text",
            )
    st.info(
        "🔐 Đăng nhập xác thực thật bằng JWT: mật khẩu được hash bằng bcrypt, "
        "token có thời hạn và được decode lại ở mỗi trang để xác định quyền hạn."
    )


# --- Xử lý Single Sign-On (SSO) từ CRM nếu có token trong query params ---
query_params = st.query_params
if "token" in query_params:
    from auth.session import verify_crm_session, login_sso_user
    crm_token = query_params["token"]
    is_valid, user_data = verify_crm_session(crm_token)
    if is_valid:
        local_token = login_sso_user(user_data)
        if local_token:
            st.session_state["token"] = local_token
            st.query_params.clear()
            st.rerun()

# --- Kiểm tra JWT token trong session ---
token = st.session_state.get("token")
payload = decode_access_token(token) if token else None

if not payload:
    if token:
        st.session_state.pop("token", None)
        st.warning("⏰ Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại.")
    show_login()
    st.stop()

db = get_session()
current_user = db.query(SalesUser).get(int(payload["sub"]))

if not current_user or not current_user.is_active:
    db.close()
    st.session_state.pop("token", None)
    st.error("Tài khoản không còn hoạt động.")
    st.stop()

with st.sidebar:
    st.markdown(f"### 👤 {current_user.full_name}")
    st.caption(f"Vai trò: {current_user.role.value}")
    st.caption(f"Token hết hạn: {__import__('datetime').datetime.fromtimestamp(payload['exp']).strftime('%d/%m/%Y %H:%M')}")
    if st.button("Đăng xuất"):
        st.session_state.pop("token", None)
        st.rerun()
    st.divider()
    if not smtp_is_configured():
        st.warning("⚠️ SMTP chưa cấu hình (.env) — email đang ở chế độ mô phỏng.")
    st.caption("📋 Khách hàng · 📦 Sản phẩm · 📝 Báo giá · ✅ Phê duyệt · 📊 Dashboard · 🤖 AI Copilot · 📜 Hợp đồng · 📥 Import Excel · 📦 Tồn kho · ⚙️ Cài đặt")


st.title("📊 QUOTEFLOW OS")
st.subheader("AI Quotation Management System")
st.markdown(
    """
> **Khách hàng → Báo giá → Phê duyệt → Gửi khách → Đàm phán → Đơn hàng → Doanh thu**

Sử dụng menu bên trái để quản lý toàn bộ vòng đời báo giá — từ tạo, phê duyệt, gửi khách hàng
đến theo dõi chuyển đổi thành đơn hàng.
"""
)

col1, col2, col3, col4 = st.columns(4)
s = kpi.kpi_summary(db)
db.close()
col1.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng số báo giá</span><br>
        <span style="font-size: 20px; color: #1E293B; font-weight: 700;">{s["total_quotes"]}</span>
    </div>
    """,
    unsafe_allow_html=True
)
col2.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Tổng giá trị báo giá</span><br>
        <span style="font-size: 19px; color: #1E293B; font-weight: 700; white-space: nowrap;">{s['total_value']:,.0f} đ</span>
    </div>
    """,
    unsafe_allow_html=True
)
col3.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Win Rate</span><br>
        <span style="font-size: 20px; color: #16A34A; font-weight: 700;">{s["win_rate"]}%</span>
    </div>
    """,
    unsafe_allow_html=True
)
col4.markdown(
    f"""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; min-height: 80px;">
        <span style="font-size: 13px; color: #64748B; font-weight: 500;">Báo giá quá hạn</span><br>
        <span style="font-size: 20px; color: {'#DC2626' if s['overdue_count'] > 0 else '#1E293B'}; font-weight: 700;">{s["overdue_count"]}</span>
    </div>
    """,
    unsafe_allow_html=True
)
