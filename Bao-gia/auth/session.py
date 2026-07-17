import streamlit as st
from database.db import get_session
from models.models import SalesUser, RoleEnum
from auth.jwt_service import decode_access_token, create_access_token
import sqlite3
import os
import datetime


def verify_crm_session(token):
    """
    Xác thực token từ cơ sở dữ liệu session của CRM (nexus_crm.db).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crm_db_path = os.path.abspath(os.path.join(base_dir, "..", "CRM-Python", "nexus_crm.db"))
    
    if not os.path.exists(crm_db_path):
        crm_db_path = os.path.abspath(os.path.join(base_dir, "NEXUS-CRM", "CRM-Python", "nexus_crm.db"))
        if not os.path.exists(crm_db_path):
            return False, None
            
    conn = sqlite3.connect(crm_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM sessions WHERE token = ?", (token,))
        session = cursor.fetchone()
        if not session:
            return False, None
            
        expires_at = datetime.datetime.fromisoformat(session["expiresAt"])
        if expires_at < datetime.datetime.now():
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return False, None
            
        return True, {
            "email": session["email"],
            "role": session["role"],
            "name": session["name"]
        }
    except Exception as e:
        print(f"[SSO ERROR] Failed to verify CRM session: {e}")
        return False, None
    finally:
        conn.close()


def login_sso_user(user_data):
    """
    Đăng nhập hoặc tạo mới SalesUser từ thông tin CRM session.
    """
    email = user_data["email"]
    name = user_data["name"]
    crm_role = user_data["role"]
    
    # Kiểm tra bản quyền công ty sở hữu qua License File (Ký số RSA)
    from auth.license_service import verify_license
    is_lic_valid, lic_data, lic_error = verify_license()
    
    owner_email = ""
    if lic_data:
        owner_email = lic_data.get("domain", "").strip().lower()
    else:
        if "Không tìm thấy file bản quyền" not in str(lic_error):
            print(f"[SSO BLOCK] License error: {lic_error}")
            return None
        import os
        owner_email = os.getenv("OWNER_COMPANY_EMAIL", "").strip().lower()
        
    if owner_email:
        email_clean = email.strip().lower()
        is_match = False
        if owner_email.startswith("@"):
            is_match = email_clean.endswith(owner_email)
        else:
            is_match = (email_clean == owner_email)
        if not is_match:
            print(f"[SSO BLOCK] User {email} does not match owner company criteria ({owner_email})")
            return None
    
    # Map roles
    role_mapping = {
        "Admin": RoleEnum.ADMIN,
        "Manager": RoleEnum.SALES_MANAGER,
        "Sale": RoleEnum.SALESMAN
    }
    role = role_mapping.get(crm_role, RoleEnum.SALESMAN)
    
    db_sess = get_session()
    try:
        user = db_sess.query(SalesUser).filter(SalesUser.username == email).first()
        if not user:
            user = SalesUser(
                username=email,
                full_name=name,
                role=role,
                email=email,
                is_active=True,
                created_at=datetime.datetime.utcnow()
            )
            db_sess.add(user)
            db_sess.commit()
            db_sess.refresh(user)
            
        token = create_access_token(user.id, user.username, user.role.value)
        return token
    except Exception as e:
        print(f"[SSO ERROR] Failed to login SSO user: {e}")
        return None
    finally:
        db_sess.close()


def require_login():
    """
    Gọi ở đầu mỗi trang Streamlit. Decode JWT token trong session_state,
    trả về đối tượng SalesUser hiện tại. Nếu token thiếu/sai/hết hạn -> chặn trang.
    Hỗ trợ Single Sign-On (SSO) từ CRM.
    """
    from config.theme import apply_custom_theme
    apply_custom_theme()
    
    # Xử lý Single Sign-On (SSO) từ CRM nếu có token trong query params
    query_params = st.query_params
    if "token" in query_params:
        crm_token = query_params["token"]
        is_valid, user_data = verify_crm_session(crm_token)
        if is_valid:
            local_token = login_sso_user(user_data)
            if local_token:
                st.session_state["token"] = local_token
                st.query_params.clear()
                st.rerun()
                
    token = st.session_state.get("token")
    payload = decode_access_token(token) if token else None

    if not payload:
        st.warning("⏰ Phiên đăng nhập không hợp lệ hoặc đã hết hạn. Vui lòng quay lại trang chính để đăng nhập.")
        st.stop()

    db = get_session()
    user = db.query(SalesUser).get(int(payload["sub"]))
    db.close()

    if not user or not user.is_active:
        st.error("Tài khoản không còn hoạt động.")
        st.stop()

    # Kiểm tra bản quyền công ty sở hữu qua License File (Ký số RSA)
    from auth.license_service import verify_license, show_activation_screen
    is_lic_valid, lic_data, lic_error = verify_license()
    if not is_lic_valid:
        st.session_state.pop("token", None)
        show_activation_screen(lic_error)
        
    owner_email = lic_data.get("domain", "").strip().lower()
    if owner_email and user.email:
        user_email_clean = user.email.strip().lower()
        is_match = False
        if owner_email.startswith("@"):
            is_match = user_email_clean.endswith(owner_email)
        else:
            is_match = (user_email_clean == owner_email)
        if not is_match:
            st.error(f"❌ Tài khoản không thuộc Công ty đăng ký bản quyền sử dụng phần mềm này (yêu cầu email khớp {owner_email}).")
            st.session_state.pop("token", None)
            st.stop()

    # Hiển thị thông tin người dùng và nút Đăng xuất ở sidebar cho mọi trang con
    with st.sidebar:
        st.markdown(f"### 👤 {user.full_name}")
        st.caption(f"Vai trò: {user.role.value}")
        import datetime
        exp_time = datetime.datetime.fromtimestamp(payload['exp']).strftime('%d/%m/%Y %H:%M')
        st.caption(f"Token hết hạn: {exp_time}")
        if st.button("Đăng xuất", key="logout_sidebar_sub_btn"):
            st.session_state.pop("token", None)
            st.rerun()
        st.divider()

    # Kiểm tra quyền truy cập Module của trang hiện tại dựa trên license
    if lic_data:
        import inspect
        current_page = ""
        for frame_info in inspect.stack():
            if "pages" in frame_info.filename or "app.py" in frame_info.filename:
                current_page = os.path.basename(frame_info.filename)
                break
                
        if current_page:
            module_mapping = {
                "10_📜_Hợp_đồng.py": "contract",
                "6_🤖_AI_Copilot.py": "copilot",
                "3_📝_Báo_giá.py": "quotation",
                "9_📦_Tồn_kho.py": "inventory",
                "1_📋_Khách_hàng.py": "crm",
                "2_📦_Sản_phẩm.py": "crm",
                "4_✅_Phê_duyệt.py": "crm",
                "5_📊_Dashboard.py": "crm",
                "7_📥_Import_Excel.py": "crm",
            }
            required_module = module_mapping.get(current_page)
            if required_module:
                licensed_modules = lic_data.get("modules", [])
                if required_module not in licensed_modules:
                    st.error(f"🚫 **Chưa cấp bản quyền**: Module '{required_module.upper()}' hiện không nằm trong danh sách bản quyền được cấp phép của bạn.")
                    st.info("Vui lòng cập nhật file bản quyền `license.lic` hợp lệ trong trang **Cài đặt**.")
                    st.stop()

    return user
