import os

class Config:
    # توکن‌ها - از متغیرهای محیطی Render خوانده می‌شوند
    NORMAL_BOT_TOKEN = os.environ.get('NORMAL_BOT_TOKEN')
    PRO_BOT_TOKEN = os.environ.get('PRO_BOT_TOKEN')
    
    # مالک
    OWNER_ID = int(os.environ.get('OWNER_ID', 0))
    
    # وب‌هوک - Render به طور خودکار URL را می‌دهد
    RENDER_EXTERNAL_URL = os.environ.get('RENDER_EXTERNAL_URL', '')
    
    # اگر RENDER_EXTERNAL_URL موجود باشد از آن استفاده کن
    if RENDER_EXTERNAL_URL:
        WEBHOOK_URL = RENDER_EXTERNAL_URL.rstrip('/')
    else:
        WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
    
    # پورت
    PORT = int(os.environ.get('PORT', 10000))
    
    # دیتابیس
    NORMAL_DB = 'normal_db.json'
    PRO_DB = 'pro_db.json'
