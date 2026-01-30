"""
فایل اصلی برای اجرای هر دو ربات روی Render
"""
import subprocess
import sys
import os
import time
import threading
from flask import Flask, jsonify

app = Flask(__name__)

# مسیر فایل‌ها
NORMAL_BOT = "normal_bot.py"
PRO_BOT = "pro_bot.py"

# فرآیندهای ربات‌ها
normal_process = None
pro_process = None

def run_bot(script_name, bot_name):
    """اجرای یک ربات"""
    try:
        print(f"🚀 در حال راه‌اندازی {bot_name}...")
        process = subprocess.Popen(
            [sys.executable, script_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # خواندن خروجی‌ها در real-time
        def read_output():
            for line in process.stdout:
                print(f"[{bot_name}] {line}", end='')
        
        threading.Thread(target=read_output, daemon=True).start()
        
        return process
    except Exception as e:
        print(f"❌ خطا در اجرای {bot_name}: {e}")
        return None

@app.route('/')
def home():
    return """
    <h1>🤖 ربات‌های ویو فعال هستند</h1>
    <p>✅ ربات Normal: در حال اجرا</p>
    <p>✅ ربات Pro: در حال اجرا</p>
    <p>📊 وضعیت: <a href="/status">مشاهده وضعیت</a></p>
    <p>🏥 سلامت: <a href="/health">بررسی سلامت</a></p>
    """

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "services": {
            "normal_bot": normal_process is not None and normal_process.poll() is None,
            "pro_bot": pro_process is not None and pro_process.poll() is None,
            "web_server": True
        }
    }), 200

@app.route('/status')
def status():
    return jsonify({
        "normal_bot": {
            "running": normal_process is not None and normal_process.poll() is None,
            "exit_code": normal_process.poll() if normal_process else None
        },
        "pro_bot": {
            "running": pro_process is not None and pro_process.poll() is None,
            "exit_code": pro_process.poll() if pro_process else None
        }
    }), 200

@app.route('/start_bots')
def start_bots():
    global normal_process, pro_process
    
    if normal_process is None or normal_process.poll() is not None:
        normal_process = run_bot(NORMAL_BOT, "Normal Bot")
    
    if os.path.exists(PRO_BOT):
        if pro_process is None or pro_process.poll() is not None:
            pro_process = run_bot(PRO_BOT, "Pro Bot")
    
    return jsonify({"message": "ربات‌ها شروع شدند"}), 200

@app.route('/restart_bots')
def restart_bots():
    global normal_process, pro_process
    
    # متوقف کردن ربات‌ها
    if normal_process:
        normal_process.terminate()
    if pro_process:
        pro_process.terminate()
    
    time.sleep(2)
    
    # راه‌اندازی مجدد
    normal_process = run_bot(NORMAL_BOT, "Normal Bot")
    
    if os.path.exists(PRO_BOT):
        pro_process = run_bot(PRO_BOT, "Pro Bot")
    
    return jsonify({"message": "ربات‌ها ری‌استارت شدند"}), 200

if __name__ == '__main__':
    print("=" * 50)
    print("🤖 در حال راه‌اندازی سرویس ربات‌های ویو...")
    print("=" * 50)
    
    # راه‌اندازی ربات‌ها در background
    normal_process = run_bot(NORMAL_BOT, "Normal Bot")
    
    if os.path.exists(PRO_BOT):
        pro_process = run_bot(PRO_BOT, "Pro Bot")
    else:
        print("⚠️ فایل pro_bot.py یافت نشد، فقط ربات Normal اجرا می‌شود.")
    
    # اجرای Flask
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
