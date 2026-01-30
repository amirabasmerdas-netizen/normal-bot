import asyncio
import logging
import os
import sqlite3
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ---------- CONFIG ----------
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", 10000))
PRO_BOT_ID = "@amele55view_bot"

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

# ---------- DATABASE ----------
db = sqlite3.connect("normal.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    inviter INTEGER,
    points INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS status (
    user_id INTEGER PRIMARY KEY,
    active INTEGER DEFAULT 0
)
""")

db.commit()

# ---------- KEYBOARD ----------
def main_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ شروع ویو", callback_data="start_view")
    kb.button(text="⏹ توقف ویو", callback_data="stop_view")
    kb.button(text="➕ افزودن کانال", callback_data="add_channel")
    kb.button(text="👥 دعوت دوستان", callback_data="referral")
    kb.button(text="🎁 هدایا", callback_data="gift")
    kb.button(text="📊 لاگ من", callback_data="log")
    kb.button(text="🚀 ارتقا به Pro", callback_data="pro")
    kb.adjust(2)
    return kb.as_markup()

# ---------- START ----------
@dp.message(CommandStart())
async def start(message: Message):
    args = message.text.split()
    user_id = message.from_user.id

    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        inviter = int(args[1]) if len(args) > 1 else None
        cur.execute("INSERT INTO users (user_id, inviter) VALUES (?,?)", (user_id, inviter))
        if inviter:
            cur.execute("UPDATE users SET points = points + 1 WHERE user_id=?", (inviter,))
        db.commit()

    await message.answer(
        "👋 خوش اومدی!\n\n"
        "ℹ️ ربات Normal فقط روی *متن و عکس* ویو می‌گیره.\n"
        "برای امکانات کامل‌تر نسخه Pro فعاله 🚀",
        reply_markup=main_kb(),
        parse_mode="Markdown"
    )

# ---------- CALLBACKS ----------
@dp.callback_query(F.data == "start_view")
async def start_view(call: CallbackQuery):
    cur.execute("INSERT OR REPLACE INTO status (user_id, active) VALUES (?,1)", (call.from_user.id,))
    db.commit()
    await call.message.answer("✅ ویو برای شما فعال شد")
    await call.answer()

@dp.callback_query(F.data == "stop_view")
async def stop_view(call: CallbackQuery):
    cur.execute("UPDATE status SET active=0 WHERE user_id=?", (call.from_user.id,))
    db.commit()
    await call.message.answer("⏹ ویو متوقف شد")
    await call.answer()

@dp.callback_query(F.data == "referral")
async def referral(call: CallbackQuery):
    me = await bot.me()
    link = f"https://t.me/{me.username}?start={call.from_user.id}"
    await call.message.answer(f"👥 لینک دعوت شما:\n\n{link}\n🎯 هر دعوت = 1 امتیاز")
    await call.answer()

@dp.callback_query(F.data == "gift")
async def gift(call: CallbackQuery):
    cur.execute("UPDATE users SET points = points + 1 WHERE user_id=?", (call.from_user.id,))
    db.commit()
    await call.message.answer("🎁 هدیه امروز دریافت شد (+1 امتیاز)")
    await call.answer()

@dp.callback_query(F.data == "log")
async def log(call: CallbackQuery):
    cur.execute("SELECT points FROM users WHERE user_id=?", (call.from_user.id,))
    points = cur.fetchone()[0]
    await call.message.answer(
        "📊 لاگ شما\n"
        "━━━━━━━━━━━━\n"
        f"⭐ امتیاز: {points}\n"
        "⚡ نسخه: Normal\n"
        "📌 ویو: متن و عکس"
    )
    await call.answer()

@dp.callback_query(F.data == "pro")
async def pro(call: CallbackQuery):
    await call.message.answer(
        "🚀 نسخه Pro فعال‌تره!\n\n"
        "✔ سرعت بیشتر\n"
        "✔ همه نوع پیام\n"
        "✔ نامحدود\n\n"
        f"🤖 ربات Pro:\n{PRO_BOT_ID}"
    )
    await call.answer()

# ---------- WEBHOOK SETUP ----------
async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()

def main():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    app.on_startup.append(lambda _: on_startup(bot))
    app.on_shutdown.append(lambda _: on_shutdown(bot))

    web.run_app(app, port=PORT)

if __name__ == "__main__":
    main()
