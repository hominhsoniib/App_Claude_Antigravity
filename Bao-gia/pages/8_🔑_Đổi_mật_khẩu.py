import streamlit as st
from database.db import get_session
from auth.session import require_login
from auth.auth_service import change_password

st.set_page_config(page_title="Đổi mật khẩu - QUOTEFLOW OS", page_icon="🔑", layout="centered")

current_user = require_login()

st.title("🔑 Đổi mật khẩu")
st.caption(f"Tài khoản: **{current_user.username}** — {current_user.full_name}")

with st.form("change_pw_form"):
    old_pw = st.text_input("Mật khẩu hiện tại", type="password")
    new_pw = st.text_input("Mật khẩu mới", type="password")
    confirm_pw = st.text_input("Nhập lại mật khẩu mới", type="password")
    submitted = st.form_submit_button("Cập nhật mật khẩu", type="primary")

if submitted:
    if new_pw != confirm_pw:
        st.error("Mật khẩu mới nhập lại không khớp.")
    else:
        db = get_session()
        user = db.merge(current_user)
        success, msg = change_password(db, user, old_pw, new_pw)
        db.close()
        if success:
            st.success(msg)
            st.info("Vui lòng đăng xuất và đăng nhập lại bằng mật khẩu mới ở trang chính.")
        else:
            st.error(msg)

st.divider()
st.caption(
    "💡 Mật khẩu nên có ít nhất 8 ký tự, kết hợp chữ hoa/thường/số để đảm bảo an toàn. "
    "Hệ thống lưu mật khẩu dưới dạng hash bcrypt, không ai (kể cả Admin) xem được mật khẩu gốc của bạn."
)
