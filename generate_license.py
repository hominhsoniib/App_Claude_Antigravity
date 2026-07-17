import os
import jwt
import datetime

# RSA Private Key của NEXUS LICENSE SERVER dùng để ký số
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQCyp2BOiWu7bX2F
4XdZtNcqgUW+C9iRl4SkBlnoeFzXzbEzBQOlB3bryJg5EmkkDXCjtZgopUd8HZKM
AuTWC+21O4NMYtQ5xv01IjTVxAi/4A3Zdzqow5GYq2ipNbGF4lU3IbWvvbf+1Dwh
Lnz9cRuKpYo0ImlJktpxNaauJIciu8pDUikQVmdIhFNfwRcmev4N4vqbzcjsh+Np
/2i047e87FnqhYjuGdXtNLJGE9o/BNfst0MM7z1aHhh3rBo+8FDho2OPYLgeNHC0
eB4yGYrc78/x7nECrnLA7AZGEr3CJVM5DbbjSb5+nEA6MG/gZJf7/E/kZPWJuuVY
rNDGGOcxAgMBAAECgf9k+JRFzwVEeS1obXW3Da5OJ6HzN16/apNc4PoPmXdfwLFV
1I+qxf1AZa8jEnS6G5596DSHRGKSk2QwHbKYB0XiGDCtC25G+WBCl4KlDpajW054
ihptJ5syXi5Y9C/RK4peDn9RRDipneoeFtgtpa+bPNRPguNe4dD0Cw6ZfauixO4H
t7XGU/n25IbOaoJDhQrnyIMK1iu9XGuQyFNyMDPNHtWQILkeVc8oQ4JfOz/Of5+S
2ZxTJKXeMxer2dsSi3Zz00hotko7RxPfIMnsDr/OwwT4bRaGEAKPkIMFO3r7px4t
zRZO9FCc8y4whbFiI46T+WUjcYwsDLh2e17qm8ECgYEA4YE2NiYPvpnz4DApZfMf
2h89Pt2WSBd9Ili8Yb2RNjqZOcRtl46ZB4paJGahosybnpqO8FstO3dCgmVsf64H
aDJ8EviSd57HZyV3mN0pyAiA7K56WqKSp9BUcUptaAp8D8GR/HshKuQwihRTVH73
rBGl0Edi+iU2ileF25KGqHECgYEAytA5YZ9YBLj4MV5cMZntO0mF69LVCe5PJLjh
BXSyyE0BYtZuIkHf0IAjzBy5xUH6w8ECScJy/RyFLiFjRjdK0sssphj4lb8c3tSj
IEfT7DSCqAW73PYDoEH1x+wQYLn4CpfOanuMNwlPNvOh0jshKsj/S8WLqSKomHdz
HL+3isECgYB6tyYZMX0/6+ebCJp+sF+VA4sAuvUdJisilcduKQrsx9a6aPp6j08X
m2KSjIdJYK8PEGzYv8VNpwi6jRcOJFZDjbWXXU3XasB4kRsURMaH5JjEM+7Bg9br
G6PYQvhmtc3thRk8nITgIm2HtqfiQ3XkXXYucaqbFcUoY5ikdIhzAQKBgQCsbVc7
niNQ8IliP50WNo2wiBOpqPeil88Fo4D8CHkvPfjdtPyxd1v3gdntYMa35B50axWs
6/qjIqo/y/cA7WVZzY7KMBS4C2FaOWHuweJ0wTgL7cQIWcg/aZSyQgqykalGKEY/
1YYiDHIigAOmHstV+sjB/NN+Go9IANYHLR+4gQKBgEnoFbG3o21OSOOdY38PFBa0
d1uzdnh3EAYQfRTD5XTkadUflZOnzAxiPi/MrSb9nfY3j4nAKmYIQ/DZOo8ZwiHf
rJNfBfNV9QffOmqP8YRfCgzBczxZRonrIZCi80smqGSm0kH8/+P44GDe5Tj+6gQx
qQjE11bjv0v/2/IJXcmE
-----END PRIVATE KEY-----"""

def make_license(company_name, tax_code, domain, email, fingerprint, days_valid, modules):
    """
    Sinh mã JWT và ghi ra file license.lic
    """
    exp_time = int((datetime.datetime.now() + datetime.timedelta(days=days_valid)).timestamp())
    payload = {
        "company_name": company_name.strip(),
        "tax_code": tax_code.strip(),
        "domain": domain.strip().lower(),
        "email": email.strip().lower(),
        "server_fingerprint": fingerprint.strip(),
        "modules": modules,
        "exp": exp_time
    }
    
    # Ký số JWT sử dụng thuật toán RS256
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="RS256")
    
    # Ghi ra file license.lic ở cả thư mục gốc và thư mục con Bao-gia
    with open("license.lic", "w", encoding="utf-8") as f:
        f.write(token)
        
    try:
        sub_lic = os.path.join("Bao-gia", "license.lic")
        with open(sub_lic, "w", encoding="utf-8") as f:
            f.write(token)
        print(f"Ghi thành công license.lic vào {sub_lic}")
    except Exception:
        pass
        
    print(f"===========================================================")
    print(f"Da sinh tep ban quyen license.lic thanh cong!")
    print(f"Cong ty: {company_name}")
    print(f"MST: {tax_code}")
    print(f"Ten mien / Email: {domain} / {email}")
    print(f"Ma van tay may chu: {fingerprint}")
    print(f"Ngay het han: {datetime.datetime.fromtimestamp(exp_time).strftime('%d/%m/%Y %H:%M')}")
    print(f"Modules: {', '.join(modules)}")
    print(f"===========================================================")

if __name__ == "__main__":
    print("--- NEXUS LICENSE SERVER GENERATION ---")
    company = input("Nhập tên Công ty sở hữu: ") or "CÔNG TY TNHH GIẢI PHÁP CÔNG NGHIỆP VIỆT"
    mst = input("Nhập mã số thuế (MST): ") or "0312345678"
    domain = input("Nhập tên miền bắt buộc (ví dụ: @company.vn): ") or "@company.vn"
    email = input("Nhập email đại diện (ví dụ: admin@company.vn): ") or "admin@company.vn"
    fingerprint = input("Nhập mã vân tay máy chủ (Fingerprint, nhập '*' để bỏ qua khóa phần cứng): ") or "*"
    days = int(input("Nhập số ngày hiệu lực (ví dụ: 365): ") or 365)
    
    # Mặc định kích hoạt full modules
    modules = ["quotation", "contract", "crm", "copilot"]
    
    make_license(company, mst, domain, email, fingerprint, days, modules)
