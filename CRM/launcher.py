import subprocess
import os
import sys

def main():
    # Tim thu muc chua file EXE dang chay
    if getattr(sys, 'frozen', False):
        current_dir = os.path.dirname(sys.executable)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    
    bat_path = os.path.join(current_dir, "chay_app.bat")
    
    if os.path.exists(bat_path):
        # Chay file bat trong boi canh thu muc do
        subprocess.call([bat_path], shell=True)
    else:
        print(f"Loi: Khong tim thay file 'chay_app.bat' tai thu muc: {current_dir}")
        print("Vui long dam bao file EXE nay nam chung thu muc voi file 'chay_app.bat'.")
        input("Nhan Enter de thoat...")

if __name__ == "__main__":
    main()
