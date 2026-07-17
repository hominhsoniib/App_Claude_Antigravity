import streamlit as st
import os
from dotenv import load_dotenv
from auth.session import require_login
from models.models import RoleEnum

st.set_page_config(page_title="Cấu hình hệ thống - QUOTEFLOW OS", page_icon="⚙️", layout="centered")

current_user = require_login()

# Chỉ cho phép Admin, CEO hoặc Giám đốc cấu hình hệ thống
if current_user.role not in [RoleEnum.ADMIN, RoleEnum.CEO, RoleEnum.SALES_DIRECTOR]:
    st.warning("🚫 Bạn không có quyền truy cập trang cấu hình hệ thống. Vui lòng liên hệ Admin/CEO.")
    st.stop()

st.title("⚙️ Cấu hình hệ thống & API")
st.caption("Quản lý khóa API cho trợ lý AI Copilot và cấu hình máy chủ gửi Email (SMTP).")

# --- PHẦN BẢN QUYỀN HỆ THỐNG ---
from auth.license_service import verify_license, get_server_fingerprint
st.write("")
st.subheader("🔑 Bản quyền hệ thống (System License)")

is_lic_valid, lic_data, lic_error = verify_license()
current_fingerprint = get_server_fingerprint()

if is_lic_valid:
    st.success("💚 **Hệ thống đã được kích hoạt bản quyền hợp lệ**")
    col_lic1, col_lic2 = st.columns(2)
    with col_lic1:
        st.markdown(f"🏢 **Công ty sở hữu**: {lic_data.get('company_name')}")
        st.markdown(f"📝 **Mã số thuế (MST)**: {lic_data.get('tax_code')}")
        st.markdown(f"🌐 **Tên miền / Email**: `{lic_data.get('domain')}` / `{lic_data.get('email')}`")
    with col_lic2:
        st.markdown(f"🖥️ **Mã vân tay máy chủ**: `{lic_data.get('server_fingerprint')}`")
        import datetime
        exp_date_str = datetime.datetime.fromtimestamp(lic_data.get('exp')).strftime('%d/%m/%Y %H:%M') if lic_data.get('exp') else "Không thời hạn"
        st.markdown(f"📅 **Ngày hết hạn**: {exp_date_str}")
        st.markdown(f"📦 **Modules đã cấp**: {', '.join(lic_data.get('modules', []))}")
else:
    st.error(f"❌ **Chưa kích hoạt bản quyền hệ thống**\n\nChi tiết lỗi: {lic_error}")
    st.info(f"🖥️ **Mã vân tay máy chủ của bạn (Server Fingerprint)**: `{current_fingerprint}`\n\nVui lòng cung cấp mã này cho nhà phát triển để nhận file `license.lic` kích hoạt phần mềm.")

uploaded_lic = st.file_uploader("Cập nhật file bản quyền mới (license.lic)", type=["lic"], key="license_file_uploader")
if uploaded_lic is not None:
    try:
        lic_content = uploaded_lic.read().decode("utf-8").strip()
        # Ghi đè file ở các vị trí
        with open("license.lic", "w", encoding="utf-8") as f:
            f.write(lic_content)
        try:
            with open(os.path.join("Bao-gia", "license.lic"), "w", encoding="utf-8") as f:
                f.write(lic_content)
        except Exception:
            pass
        st.success("🎉 Cập nhật bản quyền thành công! Đang làm mới hệ thống...")
        import time
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Lỗi đọc file: {str(e)}")

st.divider()

# Tải lại các biến môi trường hiện tại
load_dotenv(override=True)

# Hàm ghi các cấu hình vào file .env
def save_env_variables(updates: dict):
    env_path = ".env"
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
    existing_keys = {}
    for i, line in enumerate(lines):
        clean_line = line.strip()
        if clean_line and not clean_line.startswith("#") and "=" in clean_line:
            key = clean_line.split("=")[0].strip()
            existing_keys[key] = i
            
    for key, val in updates.items():
        val_str = str(val)
        if key in existing_keys:
            idx = existing_keys[key]
            lines[idx] = f"{key}={val_str}\n"
        else:
            lines.append(f"{key}={val_str}\n")
            
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

# Lấy giá trị hiện tại để hiển thị lên Form
current_gemini_key = os.getenv("GEMINI_API_KEY", "")
current_gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
current_claude_key = os.getenv("CLAUDE_API_KEY", "")
current_claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
current_owner_name = os.getenv("OWNER_COMPANY_NAME", "CÔNG TY TNHH GIẢI PHÁP CÔNG NGHIỆP VIỆT")
current_owner_mst = os.getenv("OWNER_COMPANY_MST", "0312345678")
current_owner_email = os.getenv("OWNER_COMPANY_EMAIL", "@company.vn")

current_smtp_host = os.getenv("SMTP_HOST", "")
current_smtp_port = os.getenv("SMTP_PORT", "587")
current_smtp_user = os.getenv("SMTP_USER", "")
current_smtp_pass = os.getenv("SMTP_PASSWORD", "")
current_smtp_name = os.getenv("SMTP_FROM_NAME", "QuoteFlow OS")
current_smtp_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

def validate_gemini_api_key(api_key, model):
    import urllib.request
    import urllib.error
    import json
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [
            {
                "parts": [
                    {"text": "ping"}
                ]
            }
        ]
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "candidates" in res_data:
                return True, "API Key hợp lệ."
            return False, "Không thể xác thực API Key (Phản hồi từ Google không chứa kết quả mong đợi)."
    except urllib.error.HTTPError as he:
        try:
            err_body = json.loads(he.read().decode("utf-8"))
            err_msg = err_body.get("error", {}).get("message", "")
            err_status = err_body.get("error", {}).get("status", "")
            
            if he.code == 400 and ("API_KEY_INVALID" in err_msg or "not valid" in err_msg.lower()):
                return False, "Mã lỗi HTTP 400: Gemini API Key không chính xác hoặc không hợp lệ. Vui lòng kiểm tra lại khóa API của bạn."
            elif he.code == 403:
                return False, f"Mã lỗi HTTP 403 (Forbidden): Khóa của bạn bị giới hạn quyền truy cập hoặc bị giới hạn địa lý (Ví dụ: IP Việt Nam chưa được mở quyền sử dụng cho một số dòng model). Chi tiết: {err_msg}"
            else:
                return False, f"Lỗi từ Google API (Mã lỗi {he.code}): {err_msg if err_msg else err_status}"
        except Exception:
            return False, f"Máy chủ Google phản hồi lỗi HTTP {he.code}: {he.reason}"
    except urllib.error.URLError as ue:
        return False, f"Lỗi kết nối mạng: Không thể kết nối tới máy chủ Google API. Vui lòng kiểm tra lại đường truyền internet của bạn, hoặc tắt/mở VPN/Proxy nếu có. Chi tiết: {str(ue.reason)}"
    except Exception as e:
        return False, f"Lỗi không xác định khi kết nối đến Google: {str(e)}"

def validate_claude_api_key(api_key, model):
    import urllib.request
    import urllib.error
    import json
    
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": model,
        "max_tokens": 5,
        "messages": [
            {"role": "user", "content": "ping"}
        ]
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode("utf-8"), 
        headers=headers, 
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "content" in res_data:
                return True, "API Key hợp lệ."
            return False, "Không thể xác thực API Key (Phản hồi từ Anthropic không chứa trường content mong đợi)."
    except urllib.error.HTTPError as he:
        try:
            err_body = json.loads(he.read().decode("utf-8"))
            err_type = err_body.get("error", {}).get("type", "")
            err_msg = err_body.get("error", {}).get("message", "")
            
            if he.code == 401 or "authentication" in err_type or "api_key" in err_msg.lower():
                return False, "Mã lỗi HTTP 401: Khóa API Key (x-api-key) không hợp lệ hoặc đã hết hạn. Vui lòng kiểm tra lại mã khóa bắt đầu bằng 'sk-ant-'."
            elif he.code == 404 or "not_found" in err_type or "model" in err_msg.lower() or he.code == 400:
                return False, f"Mã lỗi HTTP {he.code}: Mô hình '{model}' bạn chọn không tồn tại, không khả dụng hoặc chưa được hỗ trợ trên tài khoản của bạn. Chi tiết: {err_msg if err_msg else err_type}"
            else:
                return False, f"Lỗi phản hồi từ Anthropic API (Mã lỗi {he.code}): {err_msg if err_msg else err_type}"
        except Exception:
            if he.code == 401:
                return False, "Mã lỗi HTTP 401: Khóa API Key không chính xác (Unauthorized)."
            return False, f"Máy chủ Anthropic phản hồi lỗi HTTP {he.code}: {he.reason}"
    except urllib.error.URLError as ue:
        return False, f"Lỗi kết nối mạng: Không thể kết nối tới máy chủ Anthropic API. Vui lòng kiểm tra lại đường truyền internet của bạn, hoặc tắt/mở VPN/Proxy nếu có. Chi tiết: {str(ue.reason)}"
    except Exception as e:
        return False, f"Lỗi không xác định khi kết nối đến Anthropic: {str(e)}"

def list_available_claude_models(api_key):
    import urllib.request
    import urllib.error
    import json
    
    url = "https://api.anthropic.com/v1/models"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    req = urllib.request.Request(
        url, 
        headers=headers, 
        method="GET"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            models = [m.get("id") for m in res_data.get("data", [])]
            return True, models
    except urllib.error.HTTPError as he:
        try:
            err_body = json.loads(he.read().decode("utf-8"))
            err_msg = err_body.get("error", {}).get("message", he.reason)
            return False, f"Lỗi HTTP {he.code}: {err_msg}"
        except Exception:
            return False, f"Lỗi HTTP {he.code}: {he.reason}"
    except Exception as e:
        return False, str(e)


with st.form("settings_form"):
    # Thẻ HTML ẩn dùng để bẫy trình duyệt tự động điền mật khẩu (Autofill) vào các khóa API
    st.markdown('<div style="display:none;"><input type="text" name="fake_email_autofill"/><input type="password" name="fake_password_autofill"/></div>', unsafe_allow_html=True)

    # --- PHẦN 1: CẤU HÌNH AI COPILOT ---
    st.subheader("🤖 Cấu hình AI Copilot (Gemini API)")
    st.markdown(
        "Nhập mã khóa API Gemini của bạn để kích hoạt khả năng phân tích dữ liệu chuyên nghiệp bằng mô hình ngôn ngữ lớn (LLM). "
        "Nếu để trống, Copilot sẽ chạy ở chế độ rule-based mặc định."
    )
    
    gemini_key = st.text_input(
        "Gemini API Key", 
        value=current_gemini_key, 
        type="password",
        placeholder="Nhập mã AIzaSy..."
    )
    
    model_options = [
        "gemini-3.5-flash",
        "gemini-3.1-pro",
        "gemini-3.1-flash-lite",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    if current_gemini_model and current_gemini_model not in model_options:
        model_options.append(current_gemini_model)
        
    gemini_model = st.selectbox(
        "Tên Model Gemini",
        options=model_options,
        index=model_options.index(current_gemini_model) if current_gemini_model in model_options else 0
    )
    
    col_gemini_test, _ = st.columns([1.5, 2])
    with col_gemini_test:
        test_gemini = st.form_submit_button("🧪 Kiểm tra Gemini API Key")
        
    if test_gemini:
        gemini_key_clean = gemini_key.strip()
        gemini_model_clean = gemini_model.strip() if gemini_model.strip() else "gemini-1.5-flash"
        if not gemini_key_clean:
            st.warning("⚠️ Vui lòng nhập Gemini API Key trước khi kiểm tra.")
        else:
            with st.spinner("🔄 Đang xác thực Gemini API Key với máy chủ Google..."):
                is_valid, msg = validate_gemini_api_key(gemini_key_clean, gemini_model_clean)
            if is_valid:
                st.success("✅ Xác thực thành công: Gemini API Key hợp lệ!")
            else:
                st.error(f"❌ Xác thực thất bại: Gemini API Key không hợp lệ!\nChi tiết: {msg}")
    
    st.write("")
    st.subheader("🤖 Cấu hình Claude AI (Anthropic API)")
    st.markdown(
        "Nhập mã khóa API Claude của bạn để kích hoạt khả năng phân tích dữ liệu chuyên nghiệp bằng mô hình Claude (LLM). "
        "Nếu để trống, Copilot sẽ chạy ở chế độ Gemini hoặc rule-based mặc định."
    )
    
    claude_key = st.text_input(
        "Claude API Key", 
        value=current_claude_key, 
        type="password",
        placeholder="Nhập mã sk-ant-..."
    )
    
    claude_model_options = [
        # Các model thực tế được hỗ trợ bởi hệ thống proxy/mock của anh/chị
        "claude-sonnet-5",
        "claude-fable-5",
        "claude-opus-4-8",
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "claude-opus-4-6",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
        "claude-sonnet-4-5-20250929",
        # Các model Anthropic chính thức
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",
        "claude-3-haiku-20240307",
        "claude-3-opus-20240229"
    ]
    if current_claude_model and current_claude_model not in claude_model_options:
        claude_model_options.append(current_claude_model)
        
    claude_model = st.selectbox(
        "Tên Model Claude",
        options=claude_model_options,
        index=claude_model_options.index(current_claude_model) if current_claude_model in claude_model_options else 0
    )
    
    col_claude_test, col_claude_list = st.columns([1.5, 2])
    with col_claude_test:
        test_claude = st.form_submit_button("🧪 Kiểm tra Claude API Key")
    with col_claude_list:
        list_claude = st.form_submit_button("📋 Liệt kê Model khả dụng")
        
    if test_claude:
        claude_key_clean = claude_key.strip()
        claude_model_clean = claude_model.strip() if claude_model.strip() else "claude-3-5-sonnet-20241022"
        if not claude_key_clean:
            st.warning("⚠️ Vui lòng nhập Claude API Key trước khi kiểm tra.")
        else:
            with st.spinner("🔄 Đang xác thực Claude API Key với máy chủ Anthropic..."):
                is_valid, msg = validate_claude_api_key(claude_key_clean, claude_model_clean)
            if is_valid:
                st.success("✅ Xác thực thành công: Claude API Key hợp lệ!")
            else:
                st.error(f"❌ Xác thực thất bại: Claude API Key không hợp lệ!\nChi tiết: {msg}")
                
    if list_claude:
        claude_key_clean = claude_key.strip()
        if not claude_key_clean:
            st.warning("⚠️ Vui lòng nhập Claude API Key trước khi lấy danh sách model.")
        else:
            with st.spinner("🔄 Đang truy vấn danh sách model từ Anthropic..."):
                ok, res = list_available_claude_models(claude_key_clean)
            if ok:
                st.success("✅ Kết nối Anthropic thành công! Các model khả dụng trên tài khoản của bạn:")
                for m in res:
                    st.code(m)
            else:
                st.error(f"❌ Không thể lấy danh sách model: {res}")
    
    st.divider()
    
    # --- PHẦN 1.3: CẤU HÌNH THÔNG TIN CÔNG TY SỞ HỮU ---
    st.subheader("🏢 Cấu hình thông tin Công ty sở hữu bản quyền")
    st.markdown(
        "Khai báo thông tin Công ty đang sử dụng phần mềm. Để phục vụ mục đích bảo mật và chuyển giao: "
        "khi bàn giao cho Công ty khác sử dụng, Quản trị viên cần khai báo đúng Email/Tên miền đại diện của họ bên dưới thì tài khoản của họ mới có quyền đăng nhập và hoạt động."
    )
    
    owner_name = st.text_input(
        "Tên Công ty sở hữu", 
        value=current_owner_name,
        placeholder="Ví dụ: CÔNG TY TNHH GIẢI PHÁP CÔNG NGHIỆP VIỆT"
    )
    
    owner_mst = st.text_input(
        "Mã số thuế công ty", 
        value=current_owner_mst,
        placeholder="Ví dụ: 0312345678"
    )
    
    owner_email = st.text_input(
        "Email đại diện hoặc Tên miền (Domain)", 
        value=current_owner_email,
        placeholder="Ví dụ: admin@company.vn hoặc @company.vn"
    )
    
    st.divider()
    
    # --- PHẦN 2: CẤU HÌNH EMAIL (SMTP) ---
    st.subheader("✉️ Cấu hình gửi Email Báo giá (SMTP)")
    st.markdown(
        "Cấu hình tài khoản gửi email thật để gửi trực tiếp PDF báo giá cho khách hàng qua Email. "
        "Nếu để trống, hệ thống sẽ chạy ở chế độ **Giả lập (Simulated)**."
    )
    
    col1, col2 = st.columns(2)
    with col1:
        smtp_host = st.text_input("SMTP Host", value=current_smtp_host, placeholder="Ví dụ: smtp.gmail.com")
        smtp_port = st.text_input("SMTP Port", value=current_smtp_port, placeholder="Ví dụ: 587 hoặc 465")
        smtp_user = st.text_input("Tài khoản gửi (Email)", value=current_smtp_user, placeholder="Ví dụ: hotro@company.com")
    with col2:
        smtp_pass = st.text_input("Mật khẩu SMTP (App Password)", value=current_smtp_pass, type="password", placeholder="Nhập mật khẩu ứng dụng...")
        smtp_name = st.text_input("Tên người gửi hiển thị", value=current_smtp_name, placeholder="Ví dụ: QuoteFlow OS")
        smtp_tls = st.checkbox("Sử dụng mã hóa TLS", value=current_smtp_tls)
        
    st.write("")
    submitted = st.form_submit_button("Lưu cấu hình", type="primary", use_container_width=True)



if submitted:
    try:
        # Chuẩn bị dữ liệu cập nhật
        gemini_key_clean = gemini_key.strip()
        gemini_model_clean = gemini_model.strip() if gemini_model.strip() else "gemini-1.5-flash"
        claude_key_clean = claude_key.strip()
        claude_model_clean = claude_model.strip() if claude_model.strip() else "claude-3-5-sonnet-20241022"
        
        # Kiểm tra tính hợp lệ của Gemini API Key nếu người dùng điền vào
        if gemini_key_clean and not gemini_key_clean.startswith("your-") and gemini_key_clean != "":
            with st.spinner("🔄 Đang xác thực Gemini API Key với máy chủ Google..."):
                is_valid, msg = validate_gemini_api_key(gemini_key_clean, gemini_model_clean)
            if not is_valid:
                st.error(f"❌ Không thể lưu cấu hình: Gemini API Key không hợp lệ!\nChi tiết lỗi từ Google: {msg}")
                st.stop()
            else:
                st.toast("✅ Xác thực Gemini API Key thành công!", icon="🎉")
                
        # Kiểm tra tính hợp lệ của Claude API Key nếu người dùng điền vào
        if claude_key_clean and not claude_key_clean.startswith("your-") and claude_key_clean != "":
            with st.spinner("🔄 Đang xác thực Claude API Key với máy chủ Anthropic..."):
                is_valid, msg = validate_claude_api_key(claude_key_clean, claude_model_clean)
            if not is_valid:
                st.error(f"❌ Không thể lưu cấu hình: Claude API Key không hợp lệ!\nChi tiết lỗi từ Anthropic: {msg}")
                st.stop()
            else:
                st.toast("✅ Xác thực Claude API Key thành công!", icon="🎉")
                
        updates = {
            "GEMINI_API_KEY": gemini_key_clean,
            "GEMINI_MODEL": gemini_model_clean,
            "CLAUDE_API_KEY": claude_key_clean,
            "CLAUDE_MODEL": claude_model_clean,
            "OWNER_COMPANY_NAME": owner_name.strip(),
            "OWNER_COMPANY_MST": owner_mst.strip(),
            "OWNER_COMPANY_EMAIL": owner_email.strip(),
            "SMTP_HOST": smtp_host.strip(),
            "SMTP_PORT": smtp_port.strip(),
            "SMTP_USER": smtp_user.strip(),
            "SMTP_PASSWORD": smtp_pass.strip(),
            "SMTP_FROM_NAME": smtp_name.strip(),
            "SMTP_USE_TLS": "true" if smtp_tls else "false"
        }
        
        # Lưu vào .env
        save_env_variables(updates)
        
        # Reload variables
        load_dotenv(override=True)
        
        st.success("🎉 Đã lưu cấu hình và khởi tạo lại các thông số kết nối thành công!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Có lỗi xảy ra khi ghi cấu hình: {str(e)}")
