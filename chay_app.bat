@echo off
title NEXUS CRM & QUOTEFLOW OS - Auto Startup
echo ============================================================
echo        NEXUS CRM & QUOTEFLOW OS - KHOI DONG UNG DUNG
echo ============================================================
echo.

:: Chuyen huong vao thu muc CRM de dung moi truong ao
cd /d "%~dp0CRM"

:: Kiem tra moi truong ao .venv
if not exist .venv (
    echo [Moi] Khong tim thay moi truong ao .venv. Dang khoi tao...
    python -m venv .venv
    echo [Pip] Dang cai dat cac thu vien yeu cau...
    .venv\Scripts\pip install -r requirements.txt
) else (
    echo [Info] Kiem tra va cap nhat cac thu vien neu co...
    .venv\Scripts\pip install -r requirements.txt
)

echo.
echo ============================================================
echo   DANG KHOI DONG CAC MAY CHU...
echo   - CRM Server (FastAPI): http://127.0.0.1:8080
echo   - Quotation Server (Streamlit): http://127.0.0.1:8502
echo ============================================================
echo.

:: Khoi dong Streamlit Quotation Server tu thu muc Bao-gia, su dung venv cua CRM
echo Dang khoi dong Quotation Server (Streamlit)...
start "QUOTEFLOW OS - Sales Quotation Server" /min cmd /c "cd /d "%~dp0Bao-gia" && ..\CRM\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8502"

:: Tu dong mo trinh duyet sau 4 giay de cho cac server khoi dong xong
start "" cmd /c "timeout /t 4 >nul && start http://127.0.0.1:8080"

:: Chay server uvicorn (FastAPI CRM) trong cua so hien tai
echo Dang khoi dong CRM Server (FastAPI)...
.venv\Scripts\python -m uvicorn app:app --port 8080

pause
