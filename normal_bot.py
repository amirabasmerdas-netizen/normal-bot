import telebot
from telebot import types
import json
import os
from flask import Flask, request

# ======= تنظیمات =======import os
TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")


# ======= دیتابیس =======
DB_FILE = "normal_db.json"
if not os.path.exists(DB_FILE):
    with open(DB_FILE,"w") as f:
        json.dump({"users":{}, "channels":{}, "groups":{}},f)

def load_db():
    with open(DB_FILE,"r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE,"w") as f:
        json.dump(db,f,indent=4)

db = load_db()

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ======= کیبوردها =======
def user_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کانال")
    kb.add("▶️ شروع ویو", "⏹ توقف ویو")
    kb.add("📊 امتیاز و دوستان")
    kb.add("🎁 هدایا")
    return kb

def owner_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ اضافه کردن کانال/گروه مقصد")
    kb.add("➖ حذف کانال/گروه مقصد")
    kb.add("📋 لاگ کاربران")
    return kb

# ======= استارت =======
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    if uid == OWNER_ID:
        bot.send_message(uid,"👑 پنل مالک",reply_markup=owner_keyboard())
    else:
        bot.send_message(uid,"👋 سلام!\nاین ربات برای ویو گرفتن متن و عکس طراحی شده.\nبرای شروع پنل کاربری را ببینید.",reply_markup=user_keyboard())

# ======= دکمه‌ها =======
@bot.message_handler(func=lambda m: True)
def buttons(msg):
    uid = msg.from_user.id
    text = msg.text
    db = load_db()

    # پنل کاربر
    if uid != OWNER_ID:
        if text=="➕ افزودن کانال":
            msg = bot.send_message(uid,"لطفاً ایدی کانال با @ وارد کنید:")
            bot.register_next_step_handler(msg, add_channel)
        elif text=="▶️ شروع ویو":
            bot.send_message(uid,"✅ ویو شما شروع شد!")
        elif text=="⏹ توقف ویو":
            bot.send_message(uid,"⏹ ویو شما متوقف شد!")
        elif text=="📊 امتیاز و دوستان":
            user = db["users"].get(str(uid),{"referrals":0})
            bot.send_message(uid,f"👤 تعداد دوستان دعوت شده: {user['referrals']}")
        elif text=="🎁 هدایا":
            bot.send_message(uid,"🎁 شما می‌توانید امتیاز خود را برای هدایای ویژه استفاده کنید.")

    # پنل مالک
    else:
        if text=="➕ اضافه کردن کانال/گروه مقصد":
            msg = bot.send_message(uid,"لطفاً ایدی کانال یا گروه مقصد را با @ وارد کنید:")
            bot.register_next_step_handler(msg, add_destination)
        elif text=="➖ حذف کانال/گروه مقصد":
            msg = bot.send_message(uid,"لطفاً ایدی کانال یا گروهی که می‌خواید حذف کنید با @ وارد کنید:")
            bot.register_next_step_handler(msg, remove_destination)
        elif text=="📋 لاگ کاربران":
            text_log = ""
            for u,data in db["users"].items():
                text_log += f"👤 {u}: دعوت شده‌ها {data.get('referrals',0)}\n"
            if not text_log: text_log = "🚫 کاربری ثبت نشده"
            bot.send_message(uid,text_log)

# ======= توابع =======
def add_channel(msg):
    uid = msg.chat.id
    ch = msg.text.strip()
    db = load_db()
    if not ch.startswith("@"):
        bot.send_message(uid,"❌ ایدی کانال باید با @ شروع شود")
        return
    db["channels"][str(uid)] = ch
    save_db(db)
    bot.send_message(uid,f"✅ کانال {ch} اضافه شد!")

def add_destination(msg):
    uid = msg.chat.id
    dest = msg.text.strip()
    db = load_db()
    if not dest.startswith("@"):
        bot.send_message(uid,"❌ ایدی باید با @ شروع شود")
        return
    db["groups"][dest] = "destination"
    save_db(db)
    bot.send_message(uid,f"✅ مقصد {dest} اضافه شد!")

def remove_destination(msg):
    uid = msg.chat.id
    dest = msg.text.strip()
    db = load_db()
    if dest in db["groups"]:
        del db["groups"][dest]
        save_db(db)
        bot.send_message(uid,f"❌ مقصد {dest} حذف شد!")
    else:
        bot.send_message(uid,"مقصد یافت نشد!")

# ======= وب‌هوک =======
@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def index():
    return "Normal Bot is running!",200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0",port=10000)
