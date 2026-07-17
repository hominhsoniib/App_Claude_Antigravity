import os
import jwt
import uuid
import hashlib
import platform
import subprocess
import datetime

# RSA Public Key dùng để xác thực chữ ký số của License file
PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAsqdgTolru219heF3WbTX
KoFFvgvYkZeEpAZZ6Hhc182xMwUDpQd268iYORJpJA1wo7WYKKVHfB2SjALk1gvt
tTuDTGLUOcb9NSI01cQIv+AN2Xc6qMORmKtoqTWxheJVNyG1r723/tQ8IS58/XEb
iqWKNCJpSZLacTWmriSHIrvKQ1IpEFZnSIRTX8EXJnr+DeL6m83I7Ifjaf9otOO3
vOxZ6oWI7hnV7TSyRhPaPwTX7LdDDO89Wh4Yd6waPvBQ4aNjj2C4HjRwtHgeMhmK
3O/P8e5xAq5ywOwGRhK9wiVTOQ2240m+fpxAOjBv4GSX+/xP5GT1ibrlWKzQxhjn
MQIDAQAB
-----END PUBLIC KEY-----"""

def get_server_fingerprint():
    """
    Tạo mã vân tay phần cứng duy nhất của máy chủ để khóa bản quyền.
    Ưu tiên lấy UUID phần cứng trên Windows, nếu lỗi sẽ dùng MAC Address + Tên máy.
    """
    try:
        if platform.system() == "Windows":
            cmd = "wmic csproduct get uuid"
            output = subprocess.check_output(cmd, shell=True).decode()
            lines = [line.strip() for line in output.split("\n") if line.strip()]
            if len(lines) > 1 and "UUID" not in lines[1]:
                uuid_str = lines[1]
                return hashlib.sha256(uuid_str.encode()).hexdigest()[:16].upper()
    except Exception:
        pass
        
    # Fallback: sử dụng MAC address + node name
    try:
        mac = uuid.getnode()
        node = platform.node()
        combined = f"{mac}-{node}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16].upper()
    except Exception:
        return "GENERIC-SERVER-FINGERPRINT"

def get_license_file_path():
    """
    Tìm đường dẫn file license.lic trong thư mục hiện tại hoặc thư mục cha.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = [
        os.path.join(base_dir, "license.lic"),
        os.path.join(os.path.dirname(base_dir), "license.lic"),
        "license.lic"
    ]
    for p in paths:
        if os.path.exists(p):
            return os.path.abspath(p)
    return None

def verify_license():
    """
    Xác thực chữ ký số và nội dung của license.lic.
    Trả về (is_valid, payload, error_message).
    """
    lic_path = get_license_file_path()
    if not lic_path:
        return False, None, "Không tìm thấy file bản quyền license.lic trên máy chủ."
        
    try:
        with open(lic_path, "r", encoding="utf-8") as f:
            lic_token = f.read().strip()
            
        if not lic_token:
            return False, None, "File bản quyền license.lic rỗng."
            
        # Decode và xác thực chữ ký RSA RS256
        payload = jwt.decode(lic_token, PUBLIC_KEY, algorithms=["RS256"])
        
        # 1. Kiểm tra ngày hết hạn
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_date = datetime.datetime.fromtimestamp(exp_timestamp)
            if exp_date < datetime.datetime.now():
                return False, None, f"Bản quyền đã hết hạn vào ngày {exp_date.strftime('%d/%m/%Y')}."
                
        # 2. Kiểm tra Server Fingerprint
        expected_fingerprint = payload.get("server_fingerprint")
        if expected_fingerprint and expected_fingerprint != "*":
            current_fingerprint = get_server_fingerprint()
            if expected_fingerprint != current_fingerprint:
                return False, None, f"Bản quyền không khớp với phần cứng máy chủ này (Yêu cầu: {expected_fingerprint}, Hiện tại: {current_fingerprint})."
                
        return True, payload, None
        
    except jwt.ExpiredSignatureError:
        return False, None, "Bản quyền đã hết hạn sử dụng."
    except jwt.InvalidSignatureError:
        return False, None, "Chữ ký số bản quyền không hợp lệ. File license.lic đã bị sửa đổi trái phép."
    except jwt.DecodeError as de:
        return False, None, f"Định dạng file bản quyền không hợp lệ. Chi tiết: {str(de)}"
    except Exception as e:
        return False, None, f"Lỗi không xác định khi xác thực bản quyền: {str(e)}"

def show_activation_screen(lic_error):
    """
    Hiển thị giao diện kích hoạt bản quyền và dừng luồng chạy Streamlit.
    """
    import streamlit as st
    st.markdown(
        """
        <div style='text-align:center; padding-top: 50px;'>
            <h1 style='color:#C00000;'>🔑 YÊU CẦU KÍCH HOẠT BẢN QUYỀN</h1>
            <p style='color:#666; font-size: 15px;'>Hệ thống chưa được cấp bản quyền sử dụng hoặc bản quyền đã hết hạn.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.error(f"❌ **Lỗi bản quyền**: {lic_error}")
        
        current_fingerprint = get_server_fingerprint()
        st.info(f"🖥️ **Mã vân tay máy chủ (Server Fingerprint)**: `{current_fingerprint}`\n\nVui lòng gửi mã này cho nhà phát triển để nhận file kích hoạt.")
        
        uploaded_lic = st.file_uploader("Tải lên file bản quyền (license.lic)", type=["lic"], key="activation_license_uploader_global")
        if uploaded_lic is not None:
            try:
                lic_content = uploaded_lic.read().decode("utf-8").strip()
                # Ghi đè file
                with open("license.lic", "w", encoding="utf-8") as f:
                    f.write(lic_content)
                
                # Đồng bộ ghi đè vào các thư mục liên quan
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                for p in [os.path.join(base_dir, "license.lic"), "license.lic"]:
                    try:
                        with open(p, "w", encoding="utf-8") as f:
                            f.write(lic_content)
                    except Exception:
                        pass
                        
                st.success("🎉 Tải lên bản quyền thành công! Đang tải lại hệ thống...")
                import time
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Lỗi đọc file: {str(e)}")
                
    st.stop()
