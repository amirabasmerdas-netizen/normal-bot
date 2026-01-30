import os
import json
from aiohttp import web, ClientSession
from aiohttp.web import Response

# ================= CONFIG =================
TOKEN = os.getenv("NORMAL_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 10000))

OWNER_ID = 8321215905  # 👑 مالک

if not TOKEN:
    raise RuntimeError("NORMAL_BOT_TOKEN is not set")

API_URL = f"https://api.telegram.org/bot{TOKEN}"
DATA_FILE = "data.json"

# ================= DATA =================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "destinations": [], "referrals": {}}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

data = load_data()

# ================= TELEGRAM API =================
async def tg(method, payload=None):
    async with ClientSession() as session:
        async with session.post(f"{API_URL}/{method}", json=payload) as resp:
            return await resp.json()

async def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode":"Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    await tg("sendMessage", payload)

# ================= USER PANEL =================
def main_keyboard():
    from aiohttp.web_request import json_response
    return {
        "keyboard":[
            ["👥 افزودن دوستان", "📋 امتیاز و هدایا"],
            ["📌 لیست کانال‌ها", "▶️ شروع ویو", "⏹ توقف ویو"]
        ],
        "resize_keyboard":True
    }

# ================= OWNER PANEL =================
def owner_keyboard():
    return {
        "keyboard":[
            ["➕ افزودن کانال مقصد","➖ حذف کانال مقصد"],
            ["📋 لیست مقاصد","📄 لاگ کاربران"]
        ],
        "resize_keyboard":True
    }

# ================= HANDLERS =================
async def handle_start(chat_id):
    if str(chat_id) not in data["users"]:
        data["users"][str(chat_id)] = {"joined": True, "score":0}
        save_data()

    # پیام خوش‌آمد برای کاربران
    if chat_id != OWNER_ID:
        text = (
            "👋 خوش اومدی!\n\n"
            "🤖 این ربات Normal فعال است.\n"
            "📌 فعلاً فقط *متن و عکس* ویو می‌گیرند.\n\n"
            "💡 می‌توانید دوستانتان را دعوت کنید و امتیاز جمع کنید."
        )
        await send(chat_id, text, main_keyboard())
    else:
        await send(chat_id, "👑 پنل مالک", owner_keyboard())

# ================= OWNER COMMANDS =================
async def handle_owner(chat_id, text):
    parts = text.split()
    # افزودن مقصد
    if parts[0] == "➕ افزودن کانال مقصد":
        await send(chat_id, "لطفاً آیدی کانال مقصد را با @ ارسال کنید")
        data["awaiting_dest"] = True
        save_data()
        return
    if str(chat_id) in data.get("awaiting_dest", {}) and data["awaiting_dest"]:
        dest = text.strip()
        if not dest.startswith("@"):
            await send(chat_id, "❌ آیدی باید با @ شروع شود")
            return
        if dest in data["destinations"]:
            await send(chat_id, "⚠️ این کانال قبلاً اضافه شده")
            return
        data["destinations"].append(dest)
        data["awaiting_dest"] = False
        save_data()
        await send(chat_id, f"✅ مقصد {dest} اضافه شد")
        return

    # حذف مقصد
    if parts[0] == "➖ حذف کانال مقصد":
        await send(chat_id, "لطفاً آیدی کانال را برای حذف ارسال کنید")
        data["awaiting_remove"] = True
        save_data()
        return
    if str(chat_id) in data.get("awaiting_remove", {}) and data["awaiting_remove"]:
        dest = text.strip()
        if dest in data["destinations"]:
            data["destinations"].remove(dest)
            data["awaiting_remove"] = False
            save_data()
            await send(chat_id, f"🗑 کانال {dest} حذف شد")
        else:
            await send(chat_id, "❌ چنین کانالی وجود ندارد")
        return

    # لیست مقاصد
    if parts[0] == "📋 لیست مقاصد":
        if not data["destinations"]:
            await send(chat_id, "📭 هیچ مقصدی تنظیم نشده")
        else:
            text = "📌 مقاصد فعلی:\n" + "\n".join(data["destinations"])
            await send(chat_id, text)
        return

    # لاگ کاربران
    if parts[0] == "📄 لاگ کاربران":
        text = "👥 لیست کاربران:\n"
        for uid,u in data["users"].items():
            text += f"ID: {uid}, Score: {u.get('score',0)}\n"
        await send(chat_id, text)
        return

# ================= REFERRAL SYSTEM =================
def add_referral(user_id, ref_id):
    if ref_id == user_id:
        return
    data["referrals"].setdefault(str(ref_id), [])
    if user_id not in data["referrals"][str(ref_id)]:
        data["referrals"][str(ref_id)].append(user_id)
        data["users"][str(ref_id)]["score"] += 1
        save_data()

# ================= FORWARD MESSAGE =================
async def forward_if_allowed(message):
    if "text" not in message and "photo" not in message:
        return
    for dest in data["destinations"]:
        await tg("forwardMessage", {
            "chat_id": dest,
            "from_chat_id": message["chat"]["id"],
            "message_id": message["message_id"]
        })

# ================= WEBHOOK =================
async def webhook_handler(request):
    update = await request.json()
    if "message" not in update:
        return Response(text="ok")

    msg = update["message"]
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    text = msg.get("text","")

    # استارت
    if text.startswith("/start"):
        await handle_start(chat_id)
        return Response(text="ok")

    # مالک
    if chat_id == OWNER_ID:
        await handle_owner(chat_id, text)
        return Response(text="ok")

    # پیام کانال (مبدأ)
    if chat.get("type") == "channel":
        await forward_if_allowed(msg)
        return Response(text="ok")

    # کاربران عادی برای رفرال
    if text.startswith("/referral"):
        parts = text.split()
        if len(parts) == 2:
            ref_id = parts[1]
            add_referral(str(chat_id), str(ref_id))
            await send(chat_id, "✅ رفرال ثبت شد")
        return Response(text="ok")

    return Response(text="ok")

async def on_startup(app):
    await tg("deleteWebhook")
    await tg("setWebhook", {"url": f"{WEBHOOK_URL}/webhook"})
    print("✅ Webhook فعال شد")

# ================= RUN APP =================
app = web.Application()
app.router.add_post("/webhook", webhook_handler)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=PORT)
