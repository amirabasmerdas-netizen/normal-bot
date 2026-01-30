import os
import json
from telebot import TeleBot, types
from flask import Flask, request

# ==================== تنظیمات ====================
TOKEN_NORMAL = os.getenv("TOKEN_NORMAL")  # توکن ربات Normal
TOKEN_PRO = os.getenv("TOKEN_PRO")        # توکن ربات Pro
OWNER_ID = int(os.getenv("OWNER_ID"))    # آی‌دی مالک
WEBHOOK_URL = os.getenv("WEBHOOK_URL")   # آدرس وب‌هوک

# ==================== دیتابیس ====================
DB_FILE = "db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE,"r") as f:
            return json.load(f)
    return {"users":{}, "channels":[], "groups":[], "referrals":{}}

def save_db(db):
    with open(DB_FILE,"w") as f:
        json.dump(db,f,indent=4)

db = load_db()

# ==================== ربات ها ====================
bot_normal = TeleBot(TOKEN_NORMAL)
bot_pro = TeleBot(TOKEN_PRO)

# ==================== وب اپ برای وب هوک ====================
app = Flask(__name__)

@app.route(f"/{TOKEN_NORMAL}", methods=["POST"])
def webhook_normal():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot_normal.process_new_updates([update])
    return "OK", 200

@app.route(f"/{TOKEN_PRO}", methods=["POST"])
def webhook_pro():
    json_str = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_str)
    bot_pro.process_new_updates([update])
    return "OK", 200

# ==================== توابع عمومی ====================
def ensure_user(uid, username, first_name):
    if str(uid) not in db["users"]:
        db["users"][str(uid)] = {
            "username": username or "ندارد",
            "first_name": first_name or "نامشخص",
            "referrals": 0,
            "ref_by": None,
            "subscription": "normal",
            "points": 0
        }
        save_db(db)

def add_referral(uid, ref_id):
    if str(uid) in db["users"] and str(ref_id) in db["users"]:
        if db["users"][str(uid)]["ref_by"] is None:
            db["users"][str(uid)]["ref_by"] = str(ref_id)
            db["users"][str(ref_id)]["referrals"] += 1
            db["users"][str(ref_id)]["points"] += 1
            save_db(db)
            return True
    return False

# ==================== پنل ها ====================
def main_keyboard(user_type="normal"):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📌 کانال مبداء", "📌 کانال/گروه مقصد")
    kb.add("▶️ شروع ویو", "⏹️ توقف ویو")
    kb.add("🔗 دعوت دوستان", "🎁 هدایا")
    kb.add("📋 لاگ من", "ℹ️ راهنما")
    if user_type=="owner":
        kb.add("📋 لیست کاربران", "➕ تنظیم کانال/گروه مقصد")
    return kb

# ==================== استارت ====================
def start_bot(bot):
    @bot.message_handler(commands=["start"])
    def start(msg):
        uid = msg.from_user.id
        username = msg.from_user.username
        first_name = msg.from_user.first_name
        ensure_user(uid, username, first_name)

        # بررسی لینک رفرال
        args = msg.text.split()
        if len(args) > 1:
            ref_id = args[1]
            add_referral(uid, ref_id)

        # پیام خوش آمد
        if db["users"][str(uid)]["subscription"]=="pro":
            text = f"✨ اشتراک Pro شما فعال است! از سرعت و قابلیت‌های حرفه‌ای لذت ببرید."
        else:
            text = "✨ ربات Normal همیشه رایگان است. فقط متن و عکس ویو دریافت می‌کنید."

        bot.send_message(uid, text, reply_markup=main_keyboard("owner" if uid==OWNER_ID else "normal"))

        # اطلاع مالک
        if uid != OWNER_ID:
            bot.send_message(OWNER_ID, f"📩 کاربر @{username} با ایدی {uid} وارد ربات شد.")

# ==================== دعوت دوستان ====================
def referral_handler(bot):
    @bot.message_handler(func=lambda m: m.text=="🔗 دعوت دوستان")
    def invite(msg):
        uid = msg.from_user.id
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        ref_count = db["users"][str(uid)]["referrals"]
        text = f"🔗 لینک دعوت شما:\n{link}\n👥 دوستان دعوت شده: {ref_count}"
        bot.send_message(uid, text)

# ==================== شروع/توقف ویو ====================
def view_control(bot):
    @bot.message_handler(func=lambda m: m.text=="▶️ شروع ویو")
    def start_view(msg):
        uid = msg.from_user.id
        bot.send_message(uid,"✅ شروع ویو شد")

    @bot.message_handler(func=lambda m: m.text=="⏹️ توقف ویو")
    def stop_view(msg):
        uid = msg.from_user.id
        bot.send_message(uid,"⏹️ ویو متوقف شد")

# ==================== هدایا ====================
def gifts(bot):
    @bot.message_handler(func=lambda m: m.text=="🎁 هدایا")
    def show_gifts(msg):
        uid = msg.from_user.id
        points = db["users"][str(uid)]["points"]
        text = f"🎁 امتیاز شما: {points}\nهر ۳ امتیاز = ۱ روز اشتراک Pro رایگان!"
        bot.send_message(uid, text)

# ==================== لاگ ====================
def logs(bot):
    @bot.message_handler(func=lambda m: m.text=="📋 لاگ من")
    def my_log(msg):
        uid = msg.from_user.id
        u = db["users"][str(uid)]
        text = f"📄 لاگ شما:\n👤 نام: {u['first_name']}\n💻 یوزرنیم: @{u['username']}\n🔗 دوستان دعوت شده: {u['referrals']}\n⚡ امتیاز: {u['points']}"
        bot.send_message(uid, text)

# ==================== راهنما ====================
def help_msg(bot):
    @bot.message_handler(func=lambda m: m.text=="ℹ️ راهنما")
    def guide(msg):
        text = "📌 راهنما:\n- Normal: متن و عکس ویو\n- Pro: همه نوع پیام\n- لینک دعوت برای دریافت امتیاز و هدایا"
        bot.send_message(msg.from_user.id, text)

# ==================== ثبت کانال/گروه ====================
def owner_panel(bot):
    @bot.message_handler(func=lambda m: m.text=="📋 لیست کاربران")
    def list_users(msg):
        text = "📄 کاربران ربات:\n"
        for uid,u in db["users"].items():
            text += f"👤 @{u['username']} | ایدی: {uid} | رفرال: {u['referrals']} | امتیاز: {u['points']}\n"
        bot.send_message(msg.from_user.id, text)

# ==================== فعال سازی ربات ====================
start_bot(bot_normal)
start_bot(bot_pro)
referral_handler(bot_normal)
referral_handler(bot_pro)
view_control(bot_normal)
view_control(bot_pro)
gifts(bot_normal)
gifts(bot_pro)
logs(bot_normal)
logs(bot_pro)
help_msg(bot_normal)
help_msg(bot_pro)
owner_panel(bot_normal)
owner_panel(bot_pro)

# ==================== اجرا ====================
if __name__=="__main__":
    # ست کردن وب هوک
    bot_normal.remove_webhook()
    bot_normal.set_webhook(f"{WEBHOOK_URL}/{TOKEN_NORMAL}")
    bot_pro.remove_webhook()
    bot_pro.set_webhook(f"{WEBHOOK_URL}/{TOKEN_PRO}")
    # اجرای فلَس اپ
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
