@echo off
title Khoi dong QUOTEFLOW OS
echo ===================================================
echo Dang khoi dong QUOTEFLOW OS - AI Quotation System...
echo ===================================================

cd /d %~dp0

:: 1. Neu venv da ton tai, chay truc tiep tu venv ma khong can kiem tra python he thong
if exist venv\Scripts\python.exe (
    echo [INFO] Phat hien Virtual Environment san co.
    goto RUN_APP
)

:: 2. Kiem tra phien ban Python he thong de tao venv neu chua co
python --version >nul 2>&1
if %errorlevel% neq 0 (
    :: Thu kiem tra bang lenh 'py' (trinh khoi chay Python tren Windows)
    py --version >nul 2>&1
    if %errorlevel% eq 0 (
        set PYTHON_CMD=py
    ) else (
        echo [ERROR] Khong tim thay Python trong he thong PATH!
        echo Vui long tai va cai dat Python 3.10 tro len tai python.org (nho tich chon "Add Python to PATH" luc cai dat).
        pause
        exit /b
    )
) else (
    set PYTHON_CMD=python
)

:: 3. Tu dong tao venv moi
if not exist venv (
    echo [INFO] Dang khoi tao Virtual Environment (venv)...
    %PYTHON_CMD% -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Khong the tao Virtual Environment!
        pause
        exit /b
    )
)

:RUN_APP
:: 4. Kiem tra xem da cai dat du thu vien chua
venv\Scripts\python.exe -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Phat hien thieu thu vien. Dang tu dong cai dat tu requirements.txt...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERROR] Cai dat cac thu vien requirements.txt that bai!
        pause
        exit /b
    )
    echo [INFO] Cai dat thu vien hoan tat.
)

:: 5. Chay ung dung Streamlit
echo [1/1] Dang khoi chay Streamlit Server tai Cong 8502...
start "QUOTEFLOW OS Server" cmd /k "cd /d %~dp0 && venv\Scripts\python.exe -m streamlit run app.py --server.port 8502"

echo ===================================================
echo Da khoi chay ung dung thanh cong!
echo - Duong dan ung dung: http://localhost:8502
echo ===================================================

:: Cho 3 giay de server khoi dong roi mo trinh duyet
ping 127.0.0.1 -n 4 > nul
start "" "http://localhost:8502"
exit
