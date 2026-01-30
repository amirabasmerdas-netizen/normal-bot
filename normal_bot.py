import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import threading
import time
import os
import json
from datetime import datetime

# ایجاد یک Flask app واحد
app = Flask(__name__)

# خواندن متغیرهای محیطی
NORMAL_BOT_TOKEN = os.getenv('NORMAL_BOT_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 10000))

# کلاس دیتابیس ساده‌تر برای Render
class SimpleDB:
    def __init__(self, db_name='normal_db.json'):
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

db = SimpleDB()
bot = telebot.TeleBot(NORMAL_BOT_TOKEN)

# وب‌هوک Route
@app.route('/webhook/' + NORMAL_BOT_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'Bad Request', 400

# Route اصلی برای بررسی سلامت
@app.route('/')
def home():
    return '✅ ربات Normal در حال اجراست!', 200

@app.route('/health')
def health():
    return json.dumps({'status': 'healthy', 'service': 'normal_bot'}), 200

# دستورات ربات
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username or "ناشناس"
    
    # ذخیره کاربر
    if str(user_id) not in db.data["users"]:
        db.data["users"][str(user_id)] = {
            "id": user_id,
            "username": username,
            "first_name": message.from_user.first_name,
            "points": 0,
            "referrals": [],
            "status": "active",
            "joined": datetime.now().isoformat()
        }
        db.save()
    
    # ایجاد کیبورد
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("▶️ شروع ویو", "⏹ توقف ویو")
    markup.add("📊 امتیاز من", "👥 دعوت دوستان")
    markup.add("➕ افزودن کانال", "ℹ️ راهنما")
    
    welcome = f"""
    🤖 به ربات ویو Normal خوش آمدید!

    👤 کاربر: {username}
    🆔 آیدی: {user_id}

    ✨ امکانات:
    • افزایش ویو پیام‌های متنی و عکس
    • سیستم دعوت دوستان
    • کسب امتیاز رایگان

    🔗 لینک دعوت شما:
    https://t.me/{bot.get_me().username}?start={user_id}
    """
    
    bot.send_message(user_id, welcome, reply_markup=markup)

# Route برای تنظیم وب‌هوک
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        
        webhook_url = f"{WEBHOOK_URL}/webhook/{NORMAL_BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        
        return f'✅ وب‌هوک تنظیم شد: {webhook_url}', 200
    except Exception as e:
        return f'❌ خطا: {str(e)}', 500

# Route برای حذف وب‌هوک
@app.route('/remove_webhook', methods=['GET'])
def remove_webhook():
    try:
        bot.remove_webhook()
        return '✅ وب‌هوک حذف شد', 200
    except Exception as e:
        return f'❌ خطا: {str(e)}', 500

# اجرای برنامه
if __name__ == '__main__':
    print("🚀 در حال راه‌اندازی ربات Normal...")
    
    # تنظیم وب‌هوک
    try:
        bot.remove_webhook()
        time.sleep(2)
        
        if WEBHOOK_URL:
            webhook_url = f"{WEBHOOK_URL}/webhook/{NORMAL_BOT_TOKEN}"
            bot.set_webhook(url=webhook_url)
            print(f"✅ وب‌هوک تنظیم شد: {webhook_url}")
        else:
            print("⚠️ WEBHOOK_URL تنظیم نشده است!")
            
    except Exception as e:
        print(f"⚠️ خطا در تنظیم وب‌هوک: {e}")
    
    # اجرای Flask
    app.run(host='0.0.0.0', port=PORT, debug=False)
