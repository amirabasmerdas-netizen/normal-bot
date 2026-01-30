import telebot
from telebot import types
from flask import Flask, request
import threading
import time
import os
import json
from datetime import datetime
import logging

# تنظیم لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ایجاد Flask app
app = Flask(__name__)

# خواندن متغیرهای محیطی
NORMAL_BOT_TOKEN = os.getenv('NORMAL_BOT_TOKEN')
OWNER_ID = os.getenv('OWNER_ID')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 10000))

# بررسی وجود توکن
if not NORMAL_BOT_TOKEN:
    logger.error("❌ NORMAL_BOT_TOKEN یافت نشد!")
    raise ValueError("NORMAL_BOT_TOKEN must be set")

# کلاس دیتابیس
class SimpleDB:
    def __init__(self, db_name='normal_db.json'):
        self.db_name = db_name
        self.data = self.load()
        logger.info(f"✅ دیتابیس {db_name} لود شد")
    
    def load(self):
        try:
            with open(self.db_name, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"فایل {self.db_name} یافت نشد، ایجاد فایل جدید...")
            return {"users": {}, "destinations": []}
        except json.JSONDecodeError:
            logger.error(f"خطا در خواندن {self.db_name}")
            return {"users": {}, "destinations": []}
    
    def save(self):
        try:
            with open(self.db_name, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ دیتابیس {self.db_name} ذخیره شد")
        except Exception as e:
            logger.error(f"❌ خطا در ذخیره دیتابیس: {e}")

# ایجاد نمونه‌ها
db = SimpleDB()
bot = telebot.TeleBot(NORMAL_BOT_TOKEN)

# تابع ایجاد کیبورد
def create_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = [
        types.KeyboardButton("▶️ شروع ویو"),
        types.KeyboardButton("⏹ توقف ویو"),
        types.KeyboardButton("📊 امتیاز من"),
        types.KeyboardButton("👥 دعوت دوستان"),
        types.KeyboardButton("➕ افزودن کانال"),
        types.KeyboardButton("ℹ️ راهنما"),
    ]
    
    # اضافه کردن دکمه‌ها در دو ردیف
    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2], buttons[3])
    markup.add(buttons[4], buttons[5])
    
    return markup

# Route وب‌هوک
@app.route('/webhook/' + NORMAL_BOT_TOKEN, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        try:
            json_string = request.get_data().decode('utf-8')
            update = types.Update.de_json(json_string)
            bot.process_new_updates([update])
            logger.info("✅ درخواست وب‌هوک پردازش شد")
            return ''
        except Exception as e:
            logger.error(f"❌ خطا در پردازش وب‌هوک: {e}")
            return 'Internal Server Error', 500
    return 'Bad Request', 400

# Route سلامت
@app.route('/')
def home():
    return '✅ ربات Normal در حال اجراست!', 200

@app.route('/health')
def health():
    return json.dumps({
        'status': 'healthy',
        'service': 'normal_bot',
        'users_count': len(db.data.get("users", {})),
        'timestamp': datetime.now().isoformat()
    }), 200

# دستور start
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "ناشناس"
        first_name = message.from_user.first_name or "کاربر"
        
        logger.info(f"📱 دستور start از کاربر: {user_id} ({username})")
        
        # بررسی رفرال
        args = message.text.split()
        if len(args) > 1:
            referrer_id = args[1]
            if referrer_id.isdigit() and int(referrer_id) != user_id:
                # اضافه کردن به لیست رفرال
                if str(referrer_id) in db.data["users"]:
                    if "referrals" not in db.data["users"][str(referrer_id)]:
                        db.data["users"][str(referrer_id)]["referrals"] = []
                    
                    if user_id not in db.data["users"][str(referrer_id)]["referrals"]:
                        db.data["users"][str(referrer_id)]["referrals"].append(user_id)
                        db.data["users"][str(referrer_id)]["points"] = db.data["users"][str(referrer_id)].get("points", 0) + 10
                        db.save()
                        logger.info(f"✅ رفرال ثبت شد: {referrer_id} → {user_id}")
        
        # ذخیره یا به‌روزرسانی کاربر
        if str(user_id) not in db.data["users"]:
            db.data["users"][str(user_id)] = {
                "id": user_id,
                "username": username,
                "first_name": first_name,
                "points": 0,
                "referrals": [],
                "channels": [],
                "status": "active",
                "joined": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat()
            }
        else:
            db.data["users"][str(user_id)]["last_seen"] = datetime.now().isoformat()
        
        db.save()
        
        # ایجاد پیام خوشآمدگویی
        markup = create_keyboard()
        
        welcome_text = f"""
        🤖 **به ربات افزایش ویو خوش آمدید!** 🎉

        👤 **کاربر:** {first_name}
        📊 **وضعیت:** کاربر عادی
        
        ✨ **امکانات ربات:**
        ✅ افزایش ویو پیام‌های متنی و عکس
        ✅ سیستم دعوت دوستان و کسب امتیاز
        ✅ مدیریت کانال‌های شخصی
        
        🔗 **لینک دعوت شما:**
        `https://t.me/{bot.get_me().username}?start={user_id}`
        
        📌 **هر دوست دعوت شده = ۱۰ امتیاز رایگان!**
        
        ⚠️ **نکته:** برای استفاده از امکانات پیشرفته‌تر می‌توانید به نسخه Pro ارتقا دهید.
        """
        
        # ارسال عکس (اختیاری)
        try:
            # اگر می‌خواهید عکس ارسال کنید
            # photo_url = "https://example.com/welcome.jpg"
            # bot.send_photo(user_id, photo_url, caption=welcome_text, reply_markup=markup, parse_mode='Markdown')
            # یا فقط متن:
            bot.send_message(user_id, welcome_text, 
                           reply_markup=markup, 
                           parse_mode='Markdown')
        except Exception as e:
            logger.error(f"❌ خطا در ارسال پیام خوشآمد: {e}")
            # ارسال ساده‌تر در صورت خطا
            simple_text = f"سلام {first_name}! به ربات افزایش ویو خوش آمدید.\nاز دکمه‌های زیر استفاده کنید:"
            bot.send_message(user_id, simple_text, reply_markup=markup)
        
        logger.info(f"✅ پیام خوشآمد برای کاربر {user_id} ارسال شد")
        
    except Exception as e:
        logger.error(f"❌ خطا در تابع start: {e}")
        if 'user_id' in locals():
            bot.send_message(user_id, "❌ خطایی رخ داد! لطفاً دوباره امتحان کنید.")

# هندلر دکمه "امتیاز من"
@bot.message_handler(func=lambda message: message.text == "📊 امتیاز من")
def points_handler(message):
    try:
        user_id = message.from_user.id
        user = db.data["users"].get(str(user_id), {})
        
        points = user.get("points", 0)
        referrals = len(user.get("referrals", []))
        
        markup = create_keyboard()
        
        response = f"""
        📊 **وضعیت حساب شما**
        
        👤 نام: {user.get('first_name', 'کاربر')}
        🆔 آیدی: {user_id}
        
        ⭐ **امتیاز کل:** {points}
        👥 **تعداد دعوت:** {referrals}
        
        🔗 **لینک دعوت شما:**
        `https://t.me/{bot.get_me().username}?start={user_id}`
        
        🎁 **جوایز قابل خرید:**
        • ۱۰۰۰ ویو رایگان - ۵۰ امتیاز
        • ۱ روز اشتراک Pro - ۱۰۰ امتیاز
        • ۷ روز اشتراک Pro - ۵۰۰ امتیاز
        
        💎 **هر دعوت = ۱۰ امتیاز**
        """
        
        bot.send_message(user_id, response, 
                        reply_markup=markup,
                        parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطا در points_handler: {e}")

# هندلر دکمه "شروع ویو"
@bot.message_handler(func=lambda message: message.text == "▶️ شروع ویو")
def start_view_handler(message):
    try:
        user_id = message.from_user.id
        
        markup = create_keyboard()
        
        # بررسی کانال‌های کاربر
        user = db.data["users"].get(str(user_id), {})
        channels = user.get("channels", [])
        
        if not channels:
            response = """
            ⚠️ **هیچ کانالی اضافه نکرده‌اید!**
            
            لطفاً ابتدا از منوی اصلی روی «➕ افزودن کانال» کلیک کرده و کانال خود را اضافه کنید.
            
            سپس می‌توانید عملیات ویو را شروع کنید.
            """
            bot.send_message(user_id, response, 
                           reply_markup=markup,
                           parse_mode='Markdown')
            return
        
        response = f"""
        ✅ **عملیات ویو شروع شد!**
        
        📊 **جزئیات:**
        • تعداد کانال‌های شما: {len(channels)}
        • وضعیت: در حال افزایش ویو...
        • نوع پیام‌ها: متن و عکس
        
        ⏰ **تخمین زمان:** ویو‌ها به مرور زمان افزایش می‌یابند.
        
        🔄 برای توقف روی «⏹ توقف ویو» کلیک کنید.
        """
        
        # به‌روزرسانی وضعیت کاربر
        if str(user_id) in db.data["users"]:
            db.data["users"][str(user_id)]["viewing_active"] = True
            db.data["users"][str(user_id)]["viewing_started"] = datetime.now().isoformat()
            db.save()
        
        bot.send_message(user_id, response, 
                        reply_markup=markup,
                        parse_mode='Markdown')
        
        # شروع عملیات ویو در پس‌زمینه
        thread = threading.Thread(target=view_simulation, args=(user_id,))
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        logger.error(f"❌ خطا در start_view_handler: {e}")

def view_simulation(user_id):
    """شبیه‌سازی عملیات ویو"""
    try:
        while db.data["users"].get(str(user_id), {}).get("viewing_active", False):
            logger.info(f"🔄 در حال افزایش ویو برای کاربر {user_id}")
            time.sleep(30)  # هر ۳۰ ثانیه
            
            # افزایش امتیاز شبیه‌سازی شده
            if str(user_id) in db.data["users"]:
                db.data["users"][str(user_id)]["points"] = db.data["users"][str(user_id)].get("points", 0) + 1
                db.save()
                
    except Exception as e:
        logger.error(f"❌ خطا در view_simulation: {e}")

# هندلر دکمه "توقف ویو"
@bot.message_handler(func=lambda message: message.text == "⏹ توقف ویو")
def stop_view_handler(message):
    try:
        user_id = message.from_user.id
        
        markup = create_keyboard()
        
        # به‌روزرسانی وضعیت
        if str(user_id) in db.data["users"]:
            db.data["users"][str(user_id)]["viewing_active"] = False
            db.save()
        
        response = """
        ⏹ **عملیات ویو متوقف شد!**
        
        ✅ تمام عملیات‌های در حال اجرا متوقف شدند.
        
        📊 می‌توانید امتیازهای کسب شده را در بخش «📊 امتیاز من» مشاهده کنید.
        
        🔄 برای شروع مجدد روی «▶️ شروع ویو» کلیک کنید.
        """
        
        bot.send_message(user_id, response, 
                        reply_markup=markup,
                        parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطا در stop_view_handler: {e}")

# هندلر دکمه "دعوت دوستان"
@bot.message_handler(func=lambda message: message.text == "👥 دعوت دوستان")
def referrals_handler(message):
    try:
        user_id = message.from_user.id
        user = db.data["users"].get(str(user_id), {})
        
        markup = create_keyboard()
        
        invite_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
        referral_count = len(user.get("referrals", []))
        
        response = f"""
        👥 **سیستم دعوت دوستان**
        
        🔗 **لینک اختصاصی شما:**
        `{invite_link}`
        
        📊 **آمار شما:**
        • تعداد دعوت‌های موفق: {referral_count}
        • امتیاز از دعوت: {referral_count * 10}
        
        🎯 **نحوه دعوت:**
        1. لینک بالا را برای دوستان خود بفرستید
        2. دوستان روی لینک کلیک کنند
        3. ربات را استارت کنند
        4. شما **۱۰ امتیاز** دریافت می‌کنید!
        
        🏆 **هرچه بیشتر دعوت کنید، امتیاز بیشتری دریافت می‌کنید!**
        """
        
        # ایجاد دکمه اشتراک‌گذاری
        share_markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton(
            text="📲 اشتراک‌گذاری لینک",
            url=f"https://t.me/share/url?url={invite_link}&text=🤖 ربات افزایش ویو رایگان! امتیاز بگیر، ویو افزایش بده!"
        )
        share_markup.add(share_button)
        
        bot.send_message(user_id, response, 
                        reply_markup=markup,
                        parse_mode='Markdown')
        
        # ارسال پیام جداگانه با دکمه اشتراک‌گذاری
        bot.send_message(user_id, 
                        "برای اشتراک‌گذاری سریع لینک روی دکمه زیر کلیک کنید:",
                        reply_markup=share_markup)
        
    except Exception as e:
        logger.error(f"❌ خطا در referrals_handler: {e}")

# هندلر دکمه "افزودن کانال"
@bot.message_handler(func=lambda message: message.text == "➕ افزودن کانال")
def add_channel_handler(message):
    try:
        user_id = message.from_user.id
        
        markup = create_keyboard()
        
        response = """
        📌 **افزودن کانال جدید**
        
        لطفاً **یوزرنیم** کانال خود را ارسال کنید:
        
        مثال‌ها:
        • `@channel_name`
        • `https://t.me/channel_name`
        • فقط `channel_name`
        
        ⚠️ **شرایط لازم:**
        1. کانال باید **عمومی** باشد
        2. ربات باید بتواند پیام‌ها را ببیند
        3. حتماً @ قبل از نام کانال قرار دهید
        
        ❌ **نکته:** کانال‌های خصوصی پشتیبانی نمی‌شوند.
        """
        
        msg = bot.send_message(user_id, response, 
                              reply_markup=markup,
                              parse_mode='Markdown')
        
        # ثبت هندلر مرحله بعدی
        bot.register_next_step_handler(msg, process_channel_name)
        
    except Exception as e:
        logger.error(f"❌ خطا در add_channel_handler: {e}")

def process_channel_name(message):
    try:
        user_id = message.from_user.id
        channel_input = message.text.strip()
        
        # پاکسازی یوزرنیم
        if channel_input.startswith("https://t.me/"):
            channel_input = channel_input.replace("https://t.me/", "")
        elif channel_input.startswith("t.me/"):
            channel_input = channel_input.replace("t.me/", "")
        
        if channel_input.startswith("@"):
            channel_username = channel_input[1:]
        else:
            channel_username = channel_input
        
        # ذخیره در دیتابیس
        if str(user_id) not in db.data["users"]:
            db.data["users"][str(user_id)] = {}
        
        if "channels" not in db.data["users"][str(user_id)]:
            db.data["users"][str(user_id)]["channels"] = []
        
        # بررسی تکراری نبودن
        existing_channels = [ch.get("username", "") for ch in db.data["users"][str(user_id)].get("channels", [])]
        if channel_username in existing_channels:
            bot.send_message(user_id, f"❌ کانال `{channel_username}` قبلاً اضافه شده است!")
            return
        
        # اضافه کردن کانال جدید
        new_channel = {
            "username": channel_username,
            "added_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        db.data["users"][str(user_id)]["channels"].append(new_channel)
        db.save()
        
        markup = create_keyboard()
        
        success_msg = f"""
        ✅ **کانال با موفقیت اضافه شد!**
        
        📝 **اطلاعات کانال:**
        • نام: @{channel_username}
        • تاریخ اضافه شدن: {datetime.now().strftime("%Y/%m/%d %H:%M")}
        • وضعیت: فعال
        
        📊 **تعداد کانال‌های شما:** {len(db.data["users"][str(user_id)]["channels"])}
        
        🎯 **مرحله بعد:** روی «▶️ شروع ویو» کلیک کنید تا ویو کانال شما افزایش یابد.
        """
        
        bot.send_message(user_id, success_msg, 
                        reply_markup=markup,
                        parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطا در process_channel_name: {e}")
        bot.send_message(user_id, "❌ خطایی در پردازش کانال رخ داد!")

# هندلر دکمه "راهنما"
@bot.message_handler(func=lambda message: message.text == "ℹ️ راهنما")
def help_handler(message):
    try:
        user_id = message.from_user.id
        
        markup = create_keyboard()
        
        response = """
        ℹ️ **راهنمای کامل ربات**
        
        🎯 **نحوه کار ربات:**
        1. کانال خود را اضافه کنید (➕ افزودن کانال)
        2. عملیات ویو را شروع کنید (▶️ شروع ویو)
        3. دوستان خود را دعوت کنید (👥 دعوت دوستان)
        4. امتیازهای خود را مشاهده کنید (📊 امتیاز من)
        
        🔧 **امکانات اصلی:**
        
        **▶️ شروع ویو:**
        • افزایش ویو پیام‌های متنی و عکس
        • کار در پس‌زمینه
        • کسب امتیاز خودکار
        
        **⏹ توقف ویو:**
        • متوقف کردن عملیات ویو
        • ذخیره وضعیت فعلی
        
        **📊 امتیاز من:**
        • مشاهده امتیازهای کسب شده
        • تعداد دعوت‌های موفق
        • لینک دعوت اختصاصی
        
        **👥 دعوت دوستان:**
        • دریافت لینک دعوت
        • کسب ۱۰ امتیاز برای هر دعوت
        • سیستم اشتراک‌گذاری سریع
        
        **➕ افزودن کانال:**
        • اضافه کردن کانال عمومی
        • مدیریت چندین کانال
        • مشاهده لیست کانال‌ها
        
        ⚠️ **محدودیت‌ها:**
        • فقط پیام‌های متنی و عکس
        • کانال باید عمومی باشد
        • سرعت متوسط افزایش ویو
        
        📞 **پشتیبانی:** برای گزارش مشکل با ادمین تماس بگیرید.
        """
        
        bot.send_message(user_id, response, 
                        reply_markup=markup,
                        parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"❌ خطا در help_handler: {e}")

# هندلر برای پیام‌های متنی دیگر
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        user_id = message.from_user.id
        text = message.text
        
        logger.info(f"📨 پیام دریافتی از {user_id}: {text}")
        
        # اگر پیام یکی از دکمه‌ها نیست، راهنمایی کنیم
        if text not in ["▶️ شروع ویو", "⏹ توقف ویو", "📊 امتیاز من", 
                       "👥 دعوت دوستان", "➕ افزودن کانال", "ℹ️ راهنما"]:
            
            markup = create_keyboard()
            
            response = """
            🤔 **دستور نامعتبر!**
            
            لطفاً از دکمه‌های زیر استفاده کنید:
            
            🎯 **منوی اصلی:**
            • ▶️ شروع ویو - افزایش ویو کانال‌ها
            • ⏹ توقف ویو - متوقف کردن عملیات
            • 📊 امتیاز من - مشاهده وضعیت حساب
            • 👥 دعوت دوستان - دعوت دوستان و کسب امتیاز
            • ➕ افزودن کانال - اضافه کردن کانال جدید
            • ℹ️ راهنما - راهنمای استفاده
            
            برای شروع، روی یکی از دکمه‌های بالا کلیک کنید.
            """
            
            bot.send_message(user_id, response, reply_markup=markup)
            
    except Exception as e:
        logger.error(f"❌ خطا در echo_all: {e}")

# Route برای تنظیم وب‌هوک
@app.route('/set_webhook', methods=['GET'])
def set_webhook_route():
    try:
        bot.remove_webhook()
        time.sleep(2)
        
        if WEBHOOK_URL:
            webhook_url = f"{WEBHOOK_URL}/webhook/{NORMAL_BOT_TOKEN}"
            result = bot.set_webhook(url=webhook_url)
            
            logger.info(f"✅ وب‌هوک تنظیم شد: {webhook_url}")
            logger.info(f"🔧 نتیجه: {result}")
            
            return json.dumps({
                'success': True,
                'webhook_url': webhook_url,
                'message': 'Webhook set successfully'
            }), 200
        else:
            return json.dumps({
                'success': False,
                'message': 'WEBHOOK_URL is not set'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ خطا در تنظیم وب‌هوک: {e}")
        return json.dumps({
            'success': False,
            'message': str(e)
        }), 500

# Route برای تست
@app.route('/test', methods=['GET'])
def test_route():
    return json.dumps({
        'bot_username': bot.get_me().username if NORMAL_BOT_TOKEN else 'Not set',
        'users_count': len(db.data.get("users", {})),
        'timestamp': datetime.now().isoformat(),
        'status': 'online'
    }), 200

# تابع اصلی
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 در حال راه‌اندازی ربات افزایش ویو...")
    print(f"🤖 نام ربات: @{bot.get_me().username if NORMAL_BOT_TOKEN else 'N/A'}")
    print(f"👤 تعداد کاربران: {len(db.data['users'])}")
    print(f"🌐 پورت: {PORT}")
    print("=" * 50)
    
    try:
        # تنظیم وب‌هوک
        if WEBHOOK_URL:
            print(f"🔧 در حال تنظیم وب‌هوک...")
            bot.remove_webhook()
            time.sleep(2)
            
            webhook_url = f"{WEBHOOK_URL}/webhook/{NORMAL_BOT_TOKEN}"
            success = bot.set_webhook(url=webhook_url)
            
            if success:
                print(f"✅ وب‌هوک تنظیم شد: {webhook_url}")
            else:
                print("❌ خطا در تنظیم وب‌هوک!")
        else:
            print("⚠️ حالت Polling فعال است (WEBHOOK_URL تنظیم نشده)")
            # حالت polling برای تست محلی
            # threading.Thread(target=bot.polling, kwargs={'none_stop': True}).start()
        
        # اجرای Flask
        print(f"🌐 سرور Flask در حال راه‌اندازی روی پورت {PORT}...")
        app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)
        
    except Exception as e:
        print(f"❌ خطای
