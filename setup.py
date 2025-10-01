import os
import sys
import shutil
import winreg
from subprocess import Popen, run

PROTOCOL_NAME = "stalcal"

APP_FOLDER_NAME = "StalCal"

SHORTCUT_NAME = "StalCal"

MAIN_GAME_FILE = "main.py"

LOCAL_APP_DATA = os.getenv('LOCALAPPDATA')

INSTALL_PATH = os.path.join(LOCAL_APP_DATA, APP_FOLDER_NAME)

REG_COMMAND = f'cmd /c start "" "{sys.executable}" "{INSTALL_PATH}\\{MAIN_GAME_FILE}" \"%1\"'

def install_files():
    try:
        if os.path.exists(INSTALL_PATH):
            print(f"Папка {INSTALL_PATH} уже существует")
        
        os.makedirs(INSTALL_PATH, exist_ok=True)
        print(f"✅ Create Game Folder on: {INSTALL_PATH}")

        source_dir = os.path.dirname(os.path.abspath(__file__))
        for item in os.listdir(source_dir):
            s = os.path.join(source_dir, item)
            d = os.path.join(INSTALL_PATH, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, False, None)
            else:
                shutil.copy2(s, d)
        
        print(f"✅ Game Download Complete.")

    except Exception as e:
        print(f"❌ Error on copy game files. {e}")
        sys.exit(1)

def register_protocol():
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\{PROTOCOL_NAME}')

        winreg.SetValue(key, None, winreg.REG_SZ, f"URL:{PROTOCOL_NAME} Protocol")
        winreg.SetValue(key, "URL Protocol", winreg.REG_SZ, "")
        winreg.CloseKey(key)

        command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f'Software\\Classes\\{PROTOCOL_NAME}\\shell\\open\\command')
        winreg.SetValue(command_key, None, winreg.REG_SZ, REG_COMMAND)
        winreg.CloseKey(command_key)

        print(f"✅ protocoll '{PROTOCOL_NAME}://' succesfully registred.")

    except Exception as e:
        print(f"❌ Error on register protocoll {e}")
        print("pypiwin32 not installed.")
    except Exception as e:
        print(f"❌ Error on register protocoll {e}")
        print("maybe, no rights.")


def install_dependencies():
    packages = ["ursina", "python-socketio", "python-socketio[client], pypiwin32"]
    
    print("\n--- Установка зависимостей ---")
    
    try:
        result = run([sys.executable, "-m", "pip", "install", *packages], 
                     check=True, 
                     capture_output=True, 
                     text=True)
                     
        print("✅ dependensies installed sucessfully.")

    except Exception as e:
        print("❌ Error on installing dependencies. Check you internet connection or access rights.")
        print(f"Error :\n{e.stderr if hasattr(e, 'stderr') else e}")

if __name__ == "__main__":
    print("---------------------------------------")
    print(f"--- Downloader {SHORTCUT_NAME} ---")
    print(f" Installing in: {INSTALL_PATH}")
    print("---------------------------------------")

    install_dependencies()

    install_files()

    register_protocol()

    
    print("---------------------------------------")
    print("Download Complete! ✅")
    print(f"now you can use the launcher.")
    print("---------------------------------------")