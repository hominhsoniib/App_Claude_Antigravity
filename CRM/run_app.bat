@echo off
title NEXUS CRM - Startup Server
echo ============================================================
echo               NEXUS CRM - KHOI DONG UNG DUNG
echo ============================================================
echo.
echo Dang kiem tra thu muc lam viec...
cd /d "%~dp0"

if not exist .venv (
    echo [Moi] Khong tim thay moi truong ao .venv. Dang khoi tao...
    python -m venv .venv
)

echo [Pip] Dang kiem tra va cap nhat cac thu vien yeu cau...
.venv\Scripts\pip install -r requirements.txt

echo.
echo ============================================================
echo   UNG DUNG DA KHOI DONG THANH CONG!
echo   Vui long mo trinh duyet va truy cap: http://127.0.0.1:8080
echo   De DONG ung dung, nhan cu phap: Ctrl + C trong cua so nay.
echo ============================================================
echo.

.venv\Scripts\python -m uvicorn app:app --port 8080

pause
