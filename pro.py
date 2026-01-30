import telebot
from flask import Flask, request
import os
import json
from datetime import datetime

# ایجاد Flask app جداگانه
app = Flask(__name__)

# خواندن متغیرهای محیطی
PRO_BOT_TOKEN = os.getenv('PRO_BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 10001))

# کلاس دیتابیس
class ProDB:
    def __init__(self, db_name='pro_db.json'):
        self.db_name = db_name
        self.data = self.load()
    
    def load(self):
        try:
            with open(self.db_name, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"users": {}, "destinations": []}
    
    def save(self):
        with open(self.db_name, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

db = ProDB()
bot = telebot.TeleBot(PRO_BOT_TOKEN)

# وب‌هوک Route
@app.route('/pro_webhook/' + PRO_BOT_TOKEN, methods=['POST'])
def pro_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad Request', 400

# Route سلامت
@app.route('/pro_health')
def pro_health():
    return json.dumps({'status': 'healthy', 'service': 'pro_bot'}), 200

# دستور start
@bot.message_handler(commands=['start'])
def start_pro(message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    
    if str(user_id) not in db.data["users"]:
        db.data["users"][str(user_id)] = {
            "id": user_id,
            "username": username,
            "first_name": message.from_user.first_name,
            "pro_expiry": None,
            "status": "active",
            "joined": datetime.now().isoformat()
        }
        db.save()
    
    welcome = f"""
    🚀 به ربات ویو Pro خوش آمدید!

    👤 کاربر: {username}
    💎 سطح: Pro

    ✨ امکانات پیشرفته:
    • پشتیبانی از تمام رسانه‌ها
    • سرعت ویو بالا
    • لاگ حرفه‌ای
    • مدیریت نامحدود
    """
    
    bot.send_message(user_id, welcome)

# Route تنظیم وب‌هوک
@app.route('/pro/set_webhook', methods=['GET'])
def set_pro_webhook():
    try:
        bot.remove_webhook()
        import time
        time.sleep(1)
        
        webhook_url = f"{WEBHOOK_URL}/pro_webhook/{PRO_BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        
        return f'✅ وب‌هوک Pro تنظیم شد: {webhook_url}', 200
    except Exception as e:
        return f'❌ خطا: {str(e)}', 500

# اجرا
if __name__ == '__main__':
    print("🚀 در حال راه‌اندازی ربات Pro...")
    
    try:
        bot.remove_webhook()
        import time
        time.sleep(2)
        
        if WEBHOOK_URL:
            webhook_url = f"{WEBHOOK_URL}/pro_webhook/{PRO_BOT_TOKEN}"
            bot.set_webhook(url=webhook_url)
            print(f"✅ وب‌هوک Pro تنظیم شد: {webhook_url}")
        else:
            print("⚠️ WEBHOOK_URL تنظیم نشده است!")
            
    except Exception as e:
        print(f"⚠️ خطا در تنظیم وب‌هوک Pro: {e}")
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
