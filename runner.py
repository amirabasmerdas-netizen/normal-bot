import subprocess
import sys
import os

def run_bots():
    """اجرای همزمان دو ربات"""
    
    # مسیرهای فایل‌ها
    normal_bot = "normal_bot.py"
    pro_bot = "pro_bot.py"
    
    # بررسی وجود فایل‌ها
    if not os.path.exists(normal_bot):
        print(f"❌ فایل {normal_bot} یافت نشد!")
        return
    
    if not os.path.exists(pro_bot):
        print(f"⚠️ فایل {pro_bot} یافت نشد! فقط ربات Normal اجرا می‌شود.")
    
    print("🚀 در حال راه‌اندازی ربات‌ها...")
    
    # اجرای ربات Normal
    normal_process = subprocess.Popen(
        [sys.executable, normal_bot],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print("✅ ربات Normal اجرا شد")
    
    # اجرای ربات Pro اگر وجود دارد
    pro_process = None
    if os.path.exists(pro_bot):
        pro_process = subprocess.Popen(
            [sys.executable, pro_bot],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("✅ ربات Pro اجرا شد")
    
    try:
        # نمایش خروجی‌ها
        while True:
            if normal_process.poll() is not None:
                output, error = normal_process.communicate()
                print(f"❌ ربات Normal متوقف شد:\n{error}")
                break
                
            if pro_process and pro_process.poll() is not None:
                output, error = pro_process.communicate()
                print(f"❌ ربات Pro متوقف شد:\n{error}")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 توقف ربات‌ها...")
        normal_process.terminate()
        if pro_process:
            pro_process.terminate()

if __name__ == '__main__':
    run_bots()
