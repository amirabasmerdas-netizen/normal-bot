import telebot
from telebot import types
import json, os, time
from flask import Flask, request
from threading import Thread

# ================== تنظیمات ==================
TOKEN = "8251376954:AAFiVDI8CxGoxTH-Dvu23f532acZnOui7jg"
OWNER_ID = 8321215905
PRO_BOT_ID = "@amele55view_bot"

DB_FILE = "db.json"
WEBHOOK_URL = "https://normal-bot-3dno.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ================== دیتابیس ==================
def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "users": {},
            "destinations": {   # فقط مالک
                "channels": [],
                "groups": [@testbotamel]
            }
        }
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

# ================== کیبورد کاربر ==================
def user_kb():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کانال")
    kb.add("▶️ شروع ویو", "⏹ توقف ویو")
    kb.add("👥 دعوت دوستان", "🎁 هدایا")
    kb.add("📊 لاگ من", "📞 ارتباط با ادمین")
    return kb

# ================== استارت ==================
@bot.message_handler(commands=["start"])
def start(msg):
    db = load_db()
    uid = str(msg.from_user.id)

    # رفرال
    args = msg.text.split()
    if len(args) > 1:
        inviter = args[1]
        if inviter != uid and inviter in db["users"]:
            db["users"][inviter]["points"] += 1
            db["users"][inviter]["invites"] += 1
            bot.send_message(int(inviter),
                "🎉 یک کاربر با لینک دعوت شما وارد شد\n⭐ +1 امتیاز")

    if uid not in db["users"]:
        db["users"][uid] = {
            "channel": None,
            "view": False,
            "points": 0,
            "invites": 0,
            "last_bonus": 0,
            "pro_until": 0
        }

    save_db(db)

    bot.send_message(
        msg.chat.id,
        "👋 خوش اومدی به ربات ویو زن\n\n"
        "ℹ️ در نسخه رایگان فقط:\n"
        "📝 متن\n"
        "🖼 عکس\n"
        "ویو می‌گیرن.\n\n"
        "🎁 با دعوت دوستان می‌تونی اشتراک Pro بگیری 🚀",
        reply_markup=user_kb()
    )

# ================== افزودن کانال مبدأ ==================
@bot.message_handler(func=lambda m: m.text == "➕ افزودن کانال")
def add_channel(m):
    bot.send_message(
        m.chat.id,
        "📢 آیدی کانال مبدأ را ارسال کنید\n"
        "نمونه:\n@mychannel\n\n"
        "⚠️ ربات باید ادمین کانال باشد"
    )
    bot.register_next_step_handler(m, save_channel)

def save_channel(m):
    if not m.text.startswith("@"):
        bot.send_message(m.chat.id, "❌ آیدی باید با @ شروع شود")
        return

    try:
        member = bot.get_chat_member(m.text, bot.get_me().id)
        if member.status not in ["administrator", "creator"]:
            bot.send_message(m.chat.id, "❌ ربات ادمین کانال نیست")
            return
    except:
        bot.send_message(m.chat.id, "❌ کانال نامعتبر است")
        return

    db = load_db()
    db["users"][str(m.from_user.id)]["channel"] = m.text
    save_db(db)

    bot.send_message(
        m.chat.id,
        f"✅ کانال {m.text} ثبت شد\n"
        "▶️ حالا می‌تونی ویو رو شروع کنی"
    )

# ================== شروع / توقف ویو ==================
@bot.message_handler(func=lambda m: m.text == "▶️ شروع ویو")
def start_view(m):
    db = load_db()
    user = db["users"][str(m.from_user.id)]

    if not user["channel"]:
        bot.send_message(m.chat.id, "❌ ابتدا کانال خود را ثبت کنید")
        return

    if user["pro_until"] > time.time():
        bot.send_message(
            m.chat.id,
            "👑 اشتراک Pro برای شما فعال است\n"
            f"👉 وارد ربات Pro شوید:\n{PRO_BOT_ID}"
        )
        return

    user["view"] = True
    save_db(db)
    bot.send_message(m.chat.id, "▶️ ویو فعال شد")

@bot.message_handler(func=lambda m: m.text == "⏹ توقف ویو")
def stop_view(m):
    db = load_db()
    db["users"][str(m.from_user.id)]["view"] = False
    save_db(db)
    bot.send_message(m.chat.id, "⏹ ویو متوقف شد")

# ================== هدایا ==================
@bot.message_handler(func=lambda m: m.text == "🎁 هدایا")
def gifts(m):
    db = load_db()
    u = db["users"][str(m.from_user.id)]

    # هدیه رایگان هر 3 روز
    if time.time() - u["last_bonus"] > 259200:
        u["points"] += 1
        u["last_bonus"] = time.time()
        save_db(db)

    days = u["points"] // 3

    bot.send_message(
        m.chat.id,
        f"🎁 هدایا\n\n"
        f"⭐ امتیاز: {u['points']}\n"
        f"👥 دعوت‌ها: {u['invites']}\n\n"
        f"👑 اشتراک قابل دریافت: {days} روز Pro"
    )

# ================== لاگ ==================
@bot.message_handler(func=lambda m: m.text == "📊 لاگ من")
def log(m):
    u = load_db()["users"][str(m.from_user.id)]
    bot.send_message(
        m.chat.id,
        "━━━━━━━━━━\n"
        f"📢 کانال: {u['channel']}\n"
        f"▶️ ویو فعال: {u['view']}\n"
        f"⭐ امتیاز: {u['points']}\n"
        f"👥 دعوت‌ها: {u['invites']}\n"
        "━━━━━━━━━━"
    )

# ================== ارتباط با ادمین ==================
@bot.message_handler(func=lambda m: m.text == "📞 ارتباط با ادمین")
def support(m):
    bot.send_message(m.chat.id, f"📞 ادمین:\n@{OWNER_ID}")

# ================== ویو (متن و عکس) ==================
@bot.channel_post_handler(func=lambda m: True)
def handle_view(m):
    if not (m.text or m.photo):
        return

    db = load_db()

    for u in db["users"].values():
        if not u["view"]:
            continue
        if u["channel"] != f"@{m.chat.username}":
            continue

        for ch in db["destinations"]["channels"]:
            time.sleep(1.5)
            bot.forward_message(ch, m.chat.id, m.message_id)

        for g in db["destinations"]["groups"]:
            time.sleep(1.5)
            bot.forward_message(g, m.chat.id, m.message_id)

# ================== وب‌هوک ==================
@app.route("/", methods=["GET"])
def home():
    return "Bot is alive"

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
