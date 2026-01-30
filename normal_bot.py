import telebot
from telebot import types
import json
import os
from flask import Flask, request

TOKEN = "NORMAL_BOT_TOKEN"
OWNER_ID =   # مالک اصلی
WEBHOOK_URL = "WEBHOOK_URL"  # لینک وب‌هوک ربات

# ---------- دیتابیس ----------
DB_PATH = "db_normal.json"

def load_db():
    if os.path.exists(DB_PATH):
        with open(DB_PATH, "r") as f:
            return json.load(f)
    # دیتابیس اولیه
    return {
        "owners": [OWNER_ID],
        "users": {},
        "channels": {},
        "dest_channels": {},
        "referrals": {}
    }

def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ---------- کیبوردها ----------
def user_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کانال مبداء", "🟢 شروع ویو", "🔴 توقف ویو")
    kb.add("🎁 دعوت دوستان", "📊 لاگ فعالیت")
    return kb

def owner_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کانال/گروه مقصد", "➖ حذف کانال/گروه مقصد")
    kb.add("📊 مشاهده لاگ کاربران")
    return kb

# ---------- استارت ----------
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    first = msg.from_user.first_name or "کاربر"
    # ثبت کاربر
    if str(uid) not in db["users"]:
        db["users"][str(uid)] = {
            "channels": [],
            "referrals": [],
            "points": 0
        }
        save_db(db)
    # خوش آمد
    if uid == OWNER_ID:
        bot.send_message(uid, "👑 پنل مالک فعال شد:", reply_markup=owner_keyboard())
    else:
        bot.send_message(uid, "👋 سلام {}! این ربات ویو زن متن و عکس است.\nبرای استفاده، کیبورد زیر را مشاهده کن.".format(first), reply_markup=user_keyboard(uid))

# ---------- افزودن کانال مبداء ----------
@bot.message_handler(func=lambda m: m.text == "➕ افزودن کانال مبداء")
def add_source_channel(msg):
    uid = msg.from_user.id
    bot.send_message(uid, "لطفاً آیدی کانال با @ ارسال کنید (مثال: @examplechannel):")
    bot.register_next_step_handler(msg, save_source_channel)

def save_source_channel(msg):
    uid = msg.from_user.id
    ch = msg.text.strip()
    if not ch.startswith("@"):
        bot.send_message(uid, "❌ آیدی کانال باید با @ شروع شود.")
        return
    db["users"][str(uid)]["channels"].append(ch)
    save_db(db)
    bot.send_message(uid, f"✅ کانال مبداء {ch} ثبت شد!")

# ---------- افزودن کانال/گروه مقصد (مالک) ----------
@bot.message_handler(func=lambda m: m.text == "➕ افزودن کانال/گروه مقصد" and m.from_user.id == OWNER_ID)
def add_dest_channel(msg):
    bot.send_message(OWNER_ID, "لطفاً آیدی کانال یا گروه مقصد با @ ارسال کنید:")
    bot.register_next_step_handler(msg, save_dest_channel)

def save_dest_channel(msg):
    ch = msg.text.strip()
    if not ch.startswith("@"):
        bot.send_message(OWNER_ID, "❌ آیدی باید با @ شروع شود.")
        return
    db["dest_channels"][ch] = True
    save_db(db)
    bot.send_message(OWNER_ID, f"✅ مقصد {ch} ثبت شد!")

# ---------- حذف کانال/گروه مقصد (مالک) ----------
@bot.message_handler(func=lambda m: m.text == "➖ حذف کانال/گروه مقصد" and m.from_user.id == OWNER_ID)
def remove_dest_channel(msg):
    bot.send_message(OWNER_ID, "لطفاً آیدی کانال یا گروه مقصد برای حذف ارسال کنید:")
    bot.register_next_step_handler(msg, del_dest_channel)

def del_dest_channel(msg):
    ch = msg.text.strip()
    if ch in db["dest_channels"]:
        del db["dest_channels"][ch]
        save_db(db)
        bot.send_message(OWNER_ID, f"❌ مقصد {ch} حذف شد.")
    else:
        bot.send_message(OWNER_ID, "❌ مقصد یافت نشد.")

# ---------- لاگ کاربران (مالک) ----------
@bot.message_handler(func=lambda m: m.text == "📊 مشاهده لاگ کاربران" and m.from_user.id == OWNER_ID)
def view_logs(msg):
    text = "📋 لاگ کاربران:\n"
    for uid, data in db["users"].items():
        text += f"🆔 {uid} | کانال‌ها: {', '.join(data['channels'])} | دوستان دعوت شده: {len(data['referrals'])} | امتیاز: {data['points']}\n"
    bot.send_message(OWNER_ID, text)

# ---------- دعوت دوستان ----------
@bot.message_handler(func=lambda m: m.text == "🎁 دعوت دوستان")
def referral(msg):
    uid = msg.from_user.id
    link = f"https://t.me/YourBotUsername?start={uid}"
    bot.send_message(uid, f"📢 لینک دعوت شما:\n{link}\n✅ هر کاربری که با این لینک وارد شود به شما امتیاز می‌دهد.")

# ---------- لاگ شخصی ----------
@bot.message_handler(func=lambda m: m.text == "📊 لاگ فعالیت")
def personal_log(msg):
    uid = str(msg.from_user.id)
    data = db["users"].get(uid)
    if data:
        text = "📋 لاگ شما:\n"
        text += f"کانال‌ها: {', '.join(data['channels'])}\n"
        text += f"دوستان دعوت شده: {len(data['referrals'])}\n"
        text += f"امتیاز: {data['points']}\n"
        bot.send_message(msg.from_user.id, text)

# ---------- شروع/توقف ویو ----------
@bot.message_handler(func=lambda m: m.text == "🟢 شروع ویو")
def start_view(msg):
    uid = str(msg.from_user.id)
    db["users"][uid]["viewing"] = True
    save_db(db)
    bot.send_message(msg.from_user.id, "✅ ویو برای کانال‌های شما فعال شد!")

@bot.message_handler(func=lambda m: m.text == "🔴 توقف ویو")
def stop_view(msg):
    uid = str(msg.from_user.id)
    db["users"][uid]["viewing"] = False
    save_db(db)
    bot.send_message(msg.from_user.id, "🛑 ویو برای کانال‌های شما متوقف شد!")

# ---------- فوروارد/ویو پیام‌ها ----------
@bot.channel_post_handler(func=lambda m: True)
def forward_channel(msg):
    # فقط متن و عکس (نسخه Normal)
    for dest in db["dest_channels"]:
        try:
            if msg.content_type in ["text", "photo"]:
                bot.forward_message(dest, msg.chat.id, msg.message_id)
        except:
            pass

# ---------- وب‌هوک برای Render ----------
@app.route("/", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

# ---------- راه‌اندازی وب‌هوک ----------
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
