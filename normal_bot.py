import os
import json
from aiohttp import web, ClientSession

# ================== CONFIG ==================
TOKEN = os.getenv("NORMAL_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

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
        "destinations": []  # کانال/گروه مقصد (فعلاً دستی)
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

# ================== HANDLERS ==================
async def handle_start(chat_id):
    if str(chat_id) not in data["users"]:
        data["users"][str(chat_id)] = {
            "joined": True
        }
        save_data()

    text = (
        "👋 خوش اومدی!\n\n"
        "🤖 این ربات نسخه Normal هست.\n"
        "📌 در حال حاضر فقط *متن و عکس* ویو می‌گیرن.\n\n"
        "🎁 با دعوت دوستان می‌تونی امتیاز بگیری\n"
        "🚀 نسخه Pro امکانات خیلی بیشتری داره"
    )

    await tg("sendMessage", {
        "chat_id": chat_id,
        "text": text
    })

async def forward_if_allowed(message):
    # فقط متن و عکس
    if not ("text" in message or "photo" in message):
        return

    for dest in data["destinations"]:
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

    # /start (حتماً جواب می‌ده)
    if "text" in msg and msg["text"].startswith("/start"):
        await handle_start(chat_id)
        return web.Response(text="ok")

    # پیام کانال
    if chat.get("type") == "channel":
        await forward_if_allowed(msg)

    return web.Response(text="ok")

# ================== STARTUP ==================
async def on_startup(app):
    # حذف وب‌هوک قبلی
    await tg("deleteWebhook")

    # ست وب‌هوک جدید
    await tg("setWebhook", {
        "url": f"{WEBHOOK_URL}/webhook"
    })

    print("✅ Webhook set successfully")

# ================== APP ==================
app = web.Application()
app.router.add_post("/webhook", webhook_handler)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
