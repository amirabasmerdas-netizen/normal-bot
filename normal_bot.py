import telebot
from telebot import types
import json
import os
import time

# ------------------- تنظیمات -------------------
TOKEN = "8251376954:AAFiVDI8CxGoxTH-Dvu23f532acZnOui7jg"
OWNER_IDS = ["8321215905"]  # شناسه مالک‌ها به رشته
DB_FILE = "db.json"

# ------------------- دیتابیس -------------------
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"users": {}, "dest_channels": [], "dest_groups": []}, f, indent=4)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=4)

db = load_db()

# ------------------- ربات -------------------
bot = telebot.TeleBot(TOKEN)

def is_owner(uid):
    return str(uid) in OWNER_IDS

# ------------------- کیبوردها -------------------
def main_keyboard(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("➕ افزودن کانال")
    kb.add("🚀 شروع ویو", "⏹ توقف ویو")
    kb.add("🎁 هدایا")
    if is_owner(uid):
        kb.add("📌 تنظیم گروه و کانال مقصد", "📋 لیست کامل")
    kb.add("🔗 دعوت دوستان")
    return kb

def yes_no_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("✅ تایید", "❌ رد")
    return kb

# ------------------- استارت -------------------
@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.from_user.id)
    args = msg.text.split()
    inviter_id = args[1] if len(args) > 1 else None

    # ثبت کاربر در دیتابیس
    if uid not in db["users"]:
        db["users"][uid] = {
            "channels": [],
            "view": False,
            "referrals": [],
            "subscription": 0,
            "join_date": int(time.time())
        }
        save_db(db)
        # اطلاع مالک
        for owner in OWNER_IDS:
            bot.send_message(owner,
                             f"👤 کاربر جدید:\nاسم: {msg.from_user.first_name}\nایدی: @{msg.from_user.username or 'ندارد'}\nآیدی عددی: {uid}")
    # ثبت رفرال
    if inviter_id and inviter_id != uid:
        if inviter_id in db["users"] and uid not in db["users"][inviter_id]["referrals"]:
            db["users"][inviter_id]["referrals"].append(uid)
            save_db(db)
            bot.send_message(inviter_id,
                             f"🎉 کاربر @{msg.from_user.username or msg.from_user.first_name} با لینک دعوت شما وارد شد!\nامتیاز شما افزایش یافت.")

    # اطلاع کاربر
    bot.send_message(uid, "🎯 خوش آمدید!\nاین ربات نسخه عادی است.\nفقط متن و عکس ویو می‌گیرند.\nبرای شروع از دکمه‌ها استفاده کنید.",
                     reply_markup=main_keyboard(uid))

# ------------------- دکمه‌ها -------------------
@bot.message_handler(func=lambda m: True)
def handle_buttons(msg):
    uid = str(msg.from_user.id)
    text = msg.text

    # اضافه کردن کانال
    if text == "➕ افزودن کانال":
        msg_ = bot.send_message(uid, "لطفاً لینک کانال خود را با @ وارد کنید:")
        bot.register_next_step_handler(msg_, add_channel)
        return

    # شروع ویو
    if text == "🚀 شروع ویو":
        db["users"][uid]["view"] = True
        save_db(db)
        bot.send_message(uid, "✅ ویو برای کانال‌های شما فعال شد.")
        return

    # توقف ویو
    if text == "⏹ توقف ویو":
        db["users"][uid]["view"] = False
        save_db(db)
        bot.send_message(uid, "⏹ ویو متوقف شد.")
        return

    # هدایا
    if text == "🎁 هدایا":
        points = len(db["users"][uid]["referrals"])
        bot.send_message(uid,
                         f"🎁 شما {points} امتیاز دارید.\nهر 3 امتیاز = 1 روز اشتراک PRO.\nلینک دعوت شما:\nhttps://t.me/{bot.get_me().username}?start={uid}")
        return

    # دعوت دوستان
    if text == "🔗 دعوت دوستان":
        points = len(db["users"][uid]["referrals"])
        bot.send_message(uid,
                         f"📢 لینک اختصاصی شما برای دعوت دوستان:\nhttps://t.me/{bot.get_me().username}?start={uid}\n\nتعداد دوستان دعوت شده: {points}")
        return

    # مالک: تنظیم گروه و کانال مقصد
    if is_owner(uid) and text == "📌 تنظیم گروه و کانال مقصد":
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("➕ اضافه کردن کانال مقصد", "➖ حذف کانال مقصد")
        kb.add("➕ اضافه کردن گروه مقصد", "➖ حذف گروه مقصد")
        bot.send_message(uid, "🛠 پنل مقصد:", reply_markup=kb)
        return

    # مالک: لیست کامل
    if is_owner(uid) and text == "📋 لیست کامل":
        txt = "📊 کاربران و کانال‌ها:\n\n"
        for u, info in db["users"].items():
            txt += f"👤 {u} - کانال‌ها: {', '.join(info['channels'])} - دوستان دعوت شده: {len(info['referrals'])}\n"
        txt += f"\n🎯 کانال‌های مقصد: {', '.join(db['dest_channels'])}\n🎯 گروه‌های مقصد: {', '.join(db['dest_groups'])}"
        bot.send_message(uid, txt)
        return

    # اضافه کردن کانال یا گروه مقصد توسط مالک
    if is_owner(uid):
        if text in ["➕ اضافه کردن کانال مقصد", "➖ حذف کانال مقصد",
                    "➕ اضافه کردن گروه مقصد", "➖ حذف گروه مقصد"]:
            msg_ = bot.send_message(uid, "لطفاً لینک @ وارد کنید:")
            bot.register_next_step_handler(msg_, lambda m, t=text: handle_dest_channel_group(m, t))
            return


# ------------------- توابع -------------------
def add_channel(msg):
    uid = str(msg.from_user.id)
    ch = msg.text.strip()
    if not ch.startswith("@"):
        bot.send_message(uid, "❌ لینک باید با @ شروع شود!")
        return
    if ch not in db["users"][uid]["channels"]:
        db["users"][uid]["channels"].append(ch)
        save_db(db)
        bot.send_message(uid, f"✅ کانال {ch} اضافه شد!")
    else:
        bot.send_message(uid, "این کانال قبلاً اضافه شده بود.")

def handle_dest_channel_group(msg, action):
    uid = str(msg.from_user.id)
    ch = msg.text.strip()
    if not ch.startswith("@"):
        bot.send_message(uid, "❌ لینک باید با @ شروع شود!")
        return
    if action == "➕ اضافه کردن کانال مقصد":
        if ch not in db["dest_channels"]:
            db["dest_channels"].append(ch)
            save_db(db)
            bot.send_message(uid, f"✅ کانال مقصد {ch} اضافه شد!")
    elif action == "➖ حذف کانال مقصد":
        if ch in db["dest_channels"]:
            db["dest_channels"].remove(ch)
            save_db(db)
            bot.send_message(uid, f"❌ کانال مقصد {ch} حذف شد!")
    elif action == "➕ اضافه کردن گروه مقصد":
        if ch not in db["dest_groups"]:
            db["dest_groups"].append(ch)
            save_db(db)
            bot.send_message(uid, f"✅ گروه مقصد {ch} اضافه شد!")
    elif action == "➖ حذف گروه مقصد":
        if ch in db["dest_groups"]:
            db["dest_groups"].remove(ch)
            save_db(db)
            bot.send_message(uid, f"❌ گروه مقصد {ch} حذف شد!")

# ------------------- ویو واقعی -------------------
@bot.channel_post_handler(func=lambda m: True)
def forward_channel(msg):
    for uid, info in db["users"].items():
        if info["view"]:
            for dest in db["dest_channels"]:
                try:
                    bot.forward_message(dest, msg.chat.id, msg.message_id)
                except: pass
            for dest in db["dest_groups"]:
                try:
                    bot.forward_message(dest, msg.chat.id, msg.message_id)
                except: pass

@bot.message_handler(func=lambda m: True)
def forward_group(msg):
    if msg.chat.type in ["group", "supergroup"]:
        for uid, info in db["users"].items():
            if info["view"]:
                for dest in db["dest_channels"]:
                    try:
                        bot.forward_message(dest, msg.chat.id, msg.message_id)
                    except: pass
                for dest in db["dest_groups"]:
                    try:
                        bot.forward_message(dest, msg.chat.id, msg.message_id)
                    except: pass

# ------------------- اجرا -------------------
# برای Render حتما وب‌هوک باشه:
bot.infinity_polling()
