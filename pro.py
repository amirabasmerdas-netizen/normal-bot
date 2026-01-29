import telebot
from telebot import types
import json, os, time
from flask import Flask, request
from threading import Thread

# ================== تنظیمات ==================
TOKEN = "8415693666:AAFO3ug6Z9HaSgvt4wTv16b_hYMP9b7SWqg"
OWNER_ID = 8321215905

DB_FILE = "pro_db.json"
WEBHOOK_URL = "https://YOUR-PRO-RENDER.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================== دیتابیس ==================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "destinations": {
                "channels": [],
                "groups": []
            }
        }
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ================== کیبورد ==================
def kb():
    k = types.ReplyKeyboardMarkup(resize_keyboard=True)
    k.add("➕ افزودن کانال")
    k.add("▶️ شروع ویو", "⏹ توقف ویو")
    k.add("📊 لاگ حرفه‌ای")
    k.add("👑 اشتراک من")
    return k

# ================== استارت ==================
@bot.message_handler(commands=["start"])
def start(m):
    db = load_db()
    uid = str(m.from_user.id)

    if uid not in db["users"]:
        db["users"][uid] = {
            "channels": [],
            "view": False,
            "joined": int(time.time())
        }
        save_db(db)

    bot.send_message(
        m.chat.id,
        "👑 خوش آمدی به ربات ویو زن PRO\n\n"
        "🚀 سرعت بالا\n"
        "📊 لاگ حرفه‌ای\n"
        "♾ بدون محدودیت\n\n"
        "⚠️ این ربات فقط برای کاربران دارای اشتراک فعال است",
        reply_markup=kb()
    )

# ================== افزودن کانال ==================
@bot.message_handler(func=lambda m: m.text == "➕ افزودن کانال")
def add_channel(m):
    bot.send_message(
        m.chat.id,
        "📢 آیدی کانال مبدأ را ارسال کنید\n"
        "مثال:\n@channelname\n\n"
        "⚠️ ربات باید ادمین باشد"
    )
    bot.register_next_step_handler(m, save_channel)

def save_channel(m):
    if not m.text.startswith("@"):
        bot.send_message(m.chat.id, "❌ آیدی نامعتبر")
        return

    try:
        member = bot.get_chat_member(m.text, bot.get_me().id)
        if member.status not in ["administrator", "creator"]:
            bot.send_message(m.chat.id, "❌ ربات ادمین نیست")
            return
    except:
        bot.send_message(m.chat.id, "❌ کانال وجود ندارد")
        return

    db = load_db()
    u = db["users"][str(m.from_user.id)]

    if m.text in u["channels"]:
        bot.send_message(m.chat.id, "⚠️ این کانال قبلاً اضافه شده")
        return

    u["channels"].append(m.text)
    save_db(db)

    bot.send_message(
        m.chat.id,
        f"✅ کانال {m.text} اضافه شد\n"
        "▶️ ویو آماده شروع است"
    )

# ================== شروع / توقف ==================
@bot.message_handler(func=lambda m: m.text == "▶️ شروع ویو")
def start_view(m):
    db = load_db()
    u = db["users"][str(m.from_user.id)]

    if not u["channels"]:
        bot.send_message(m.chat.id, "❌ هیچ کانالی ثبت نشده")
        return

    u["view"] = True
    save_db(db)
    bot.send_message(m.chat.id, "🚀 ویو PRO فعال شد")

@bot.message_handler(func=lambda m: m.text == "⏹ توقف ویو")
def stop_view(m):
    db = load_db()
    db["users"][str(m.from_user.id)]["view"] = False
    save_db(db)
    bot.send_message(m.chat.id, "⏹ ویو متوقف شد")

# ================== لاگ حرفه‌ای ==================
@bot.message_handler(func=lambda m: m.text == "📊 لاگ حرفه‌ای")
def log(m):
    u = load_db()["users"][str(m.from_user.id)]
    bot.send_message(
        m.chat.id,
        "━━━━━━━━━━━━━━━━\n"
        "📊 گزارش PRO\n\n"
        f"📢 کانال‌ها: {len(u['channels'])}\n"
        f"▶️ ویو فعال: {'✅' if u['view'] else '❌'}\n"
        f"⏱ مدت عضویت: {(time.time()-u['joined'])//86400} روز\n"
        "🚀 سرعت: حداکثری\n"
        "━━━━━━━━━━━━━━━━"
    )

# ================== ویو (همه پیام‌ها) ==================
@bot.channel_post_handler(func=lambda m: True)
def handle_all(m):
    db = load_db()

    for u in db["users"].values():
        if not u["view"]:
            continue
        if f"@{m.chat.username}" not in u["channels"]:
            continue

        for ch in db["destinations"]["channels"]:
            bot.forward_message(ch, m.chat.id, m.message_id)

        for g in db["destinations"]["groups"]:
            bot.forward_message(g, m.chat.id, m.message_id)

# ================== وب‌هوک ==================
@app.route("/", methods=["GET"])
def home():
    return "PRO bot alive"

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates(
        [telebot.types.Update.de_json(request.stream.read().decode("utf-8"))]
    )
    return "OK"

def run():
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=10000)

Thread(target=run).start()
