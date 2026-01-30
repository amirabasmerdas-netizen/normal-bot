import os
import json
import asyncio
from aiohttp import web, ClientSession

TOKEN = os.getenv("NORMAL_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

API_URL = f"https://api.telegram.org/bot{TOKEN}"

DATA_FILE = "normal_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "users": {},
        "destinations": []
    }

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

async def tg(method, payload=None):
    async with ClientSession() as session:
        async with session.post(f"{API_URL}/{method}", json=payload) as r:
            return await r.json()

async def start_handler(chat_id):
    text = (
        "👋 خوش اومدی!\n\n"
        "🤖 این ربات نسخه Normal هست.\n"
        "📌 فقط *متن و عکس* ویو می‌گیرن.\n\n"
        "🎁 با دعوت دوستان امتیاز بگیر\n"
        "🚀 برای امکانات کامل‌تر نسخه Pro در دسترسه"
    )
    await tg("sendMessage", {
        "chat_id": chat_id,
        "text": text
    })

async def handle_update(update):
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]

    if msg.get("text") == "/start":
        if str(chat_id) not in data["users"]:
            data["users"][str(chat_id)] = {
                "points": 0,
                "active": True
            }
            save_data(data)
        await start_handler(chat_id)
        return

    if msg["chat"]["type"] in ["channel"]:
        if "text" in msg or "photo" in msg:
            for dest in data["destinations"]:
                await tg("forwardMessage", {
                    "chat_id": dest,
                    "from_chat_id": msg["chat"]["id"],
                    "message_id": msg["message_id"]
                })

async def webhook(request):
    update = await request.json()
    await handle_update(update)
    return web.Response(text="ok")

async def on_startup(app):
    await tg("setWebhook", {
        "url": f"{WEBHOOK_URL}/webhook"
    })

app = web.Application()
app.router.add_post("/webhook", webhook)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, port=PORT)
