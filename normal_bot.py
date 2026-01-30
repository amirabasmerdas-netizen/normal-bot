import os
import json
from aiohttp import web, ClientSession

# ================== CONFIG ==================
TOKEN = os.getenv("NORMAL_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

OWNER_ID = 8588773170  # 👑 مالک

if not TOKEN:
    raise RuntimeError("NORMAL_BOT_TOKEN is not set")

API_URL = f"https://api.telegram.org/bot{TOKEN}"
DATA_FILE = "data.json"

# ================== DATA ==================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "users": {},
        "destinations": []  # فقط کانال مقصد
    }

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# ================== TELEGRAM API ==================
async def tg(method, payload=None):
    async with ClientSession() as session:
        async with session.post(f"{API_URL}/{method}", json=payload) as resp:
            return await resp.json()

async def send(chat_id, text):
    await tg("sendMessage", {
        "chat_id": chat_id,
        "text": text
    })

# ================== HANDLERS ==================
async def handle_start(chat_id):
    if str(chat_id) not in data["users"]:
        data["users"][str(chat_id)] = {"joined": True}
        save_data()

    text = (
        "👋 خوش اومدی!\n\n"
        "🤖 ربات Normal فعال است.\n"
        "📌 فعلاً فقط *متن و عکس* ویو می‌گیرن.\n\n"
        "ℹ️ تنظیم مقصد فقط توسط مالک انجام می‌شود."
    )
    await send(chat_id, text)

async def handle_owner_commands(chat_id, text):
    parts = text.split()

    # افزودن مقصد (فقط برای مالک)
    if parts[0] == "/add_dest" and len(parts) == 2:
        dest = parts[1]
        if not dest.startswith("@"):
            await send(chat_id, "❌ آیدی باید با @ شروع شود")
            return

        if dest in data["destinations"]:
            await send(chat_id, "⚠️ این مقصد قبلاً اضافه شده")
            return

        data["destinations"].append(dest)
        save_data()
        await send(chat_id, f"✅ مقصد {dest} اضافه شد")
        return

    # حذف مقصد (فقط برای مالک)
    if parts[0] == "/remove_dest" and len(parts) == 2:
        dest = parts[1]
        if dest in data["destinations"]:
            data["destinations"].remove(dest)
            save_data()
            await send(chat_id, f"🗑 مقصد {dest} حذف شد")
        else:
            await send(chat_id, "❌ چنین مقصدی وجود ندارد")
        return

    # لیست مقاصد (برای مالک)
    if parts[0] == "/list_dest":
        if not data["destinations"]:
            await send(chat_id, "📭 هیچ مقصدی تنظیم نشده")
        else:
            text = "📌 مقاصد فعلی:\n" + "\n".join(data["destinations"])
            await send(chat_id, text)
        return

async def forward_if_allowed(message):
    # فقط متن و عکس
    if not ("text" in message or "photo" in message):
        return

    for dest in data["destinations"]:
        # فقط کانال‌های تلگرام (dest باید با @ باشه)
        if dest.startswith("@"):
            await tg("forwardMessage", {
                "chat_id": dest,
                "from_chat_id": message["chat"]["id"],
                "message_id": message["message_id"]
            })

# ================== WEBHOOK ==================
async def webhook_handler(request):
    update = await request.json()

    if "message" not in update:
        return web.Response(text="ok")

    msg = update["message"]
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text", "")

    # /start
    if text.startswith("/start"):
        await handle_start(chat_id)
        return web.Response(text="ok")

    # دستورات مالک
    if chat_id == OWNER_ID and text.startswith("/"):
        await handle_owner_commands(chat_id, text)
        return web.Response(text="ok")

    # پیام کانال (مبدأ)
    if chat.get("type") == "channel":
        await forward_if_allowed(msg)

    return web.Response(text="ok")

# ================== STARTUP ==================
async def on_startup(app):
    await tg("deleteWebhook")
    await tg("setWebhook", {
        "url": f"{WEBHOOK_URL}/webhook"
    })
    print("✅ Webhook set")

# ================== APP ==================
app = web.Application()
app.router.add_post("/webhook", webhook_handler)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
