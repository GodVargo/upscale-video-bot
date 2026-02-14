"""
Telegram Bot Webhook для Vercel
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.parse
from urllib.error import HTTPError

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8560064127:AAESCPlqu9_ht76zTNZ6V8Z1v9SyNyvonHQ")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "")
CHANNEL_ID = os.environ.get("CHANNEL_ID")
CHANNEL_URL = os.environ.get("CHANNEL_URL")
# URL для доступа к баннеру (предполагается, что файлы из public доступны в корне)
BANNER_URL = f"{WEBAPP_URL}/subscribe_banner.jpg" if WEBAPP_URL else None

def send_telegram_request(method, data):
    """Отправка запроса к Telegram API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except HTTPError as e:
        print(f"Error calling {method}: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup
    send_telegram_request("sendMessage", data)

def send_photo(chat_id, photo_url, caption=None, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "photo": photo_url,
        "parse_mode": "HTML"
    }
    if caption:
        data["caption"] = caption
    if reply_markup:
        data["reply_markup"] = reply_markup
    send_telegram_request("sendPhoto", data)

def check_subscription(user_id):
    """Проверка подписки"""
    if not CHANNEL_ID:
        return True
    
    data = {"chat_id": CHANNEL_ID, "user_id": user_id}
    result = send_telegram_request("getChatMember", data)
    
    if result and result.get("ok"):
        status = result["result"]["status"]
        return status in ["creator", "administrator", "member", "restricted"]
    return True # В случае ошибки (например, бот не админ) пропускаем


def send_subscription_prompt(chat_id, host=""):
    # Используем WEBAPP_URL из env или собираем из host
    base_url = WEBAPP_URL or f"https://{host}"
    
    # URL картинки
    photo_url = f"{base_url}/subscribe_banner.jpg"

    reply_markup = {
        "inline_keyboard": [
            [{"text": "📢 Подписаться", "url": CHANNEL_URL or "https://t.me/"}],
            [{"text": "✅ Проверить подписку", "callback_data": "check_subscription"}]
        ]
    }
    
    caption = (
        "👋 <b>Привет!</b>\n\n"
        "Для использования бота необходимо подписаться на наш канал:\n"
        f"<b>AI Laboratory</b>\n\n"
        "После подписки нажмите кнопку «Проверить подписку»."
    )
    
    print(f"Sending prompt with photo: {photo_url}")
    # Пробуем отправить фото, если не получится - текст
    try:
         send_photo(chat_id, photo_url, caption, reply_markup)
    except Exception as e:
         print(f"Failed to send photo: {e}")
         send_message(chat_id, caption, reply_markup)


def send_welcome(chat_id, host):
    webapp_url = WEBAPP_URL or f"https://{host}"
    reply_markup = {
        "inline_keyboard": [[{
            "text": "🎬 Улучшить видео",
            "web_app": {"url": webapp_url}
        }]]
    }
    send_message(
        chat_id,
        "👋 <b>Добро пожаловать в Upscale Video Bot!</b>\n\n"
        "🎥 Этот бот улучшает качество видео с помощью AI.\n\n"
        "📱 Нажмите кнопку ниже, чтобы открыть редактор:",
        reply_markup
    )

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        update = json.loads(body)
        host = self.headers.get('Host', '')
        
        if "callback_query" in update:
            callback = update["callback_query"]
            chat_id = callback["message"]["chat"]["id"]
            user_id = callback["from"]["id"]
            data = callback.get("data")
            callback_id = callback["id"]
            message_id = callback["message"]["message_id"]

            if data == "check_subscription":
                if check_subscription(user_id):
                    # Удаляем сообщение с просьбой подписаться
                    send_telegram_request("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
                    send_welcome(chat_id, host)
                else:
                    send_telegram_request("answerCallbackQuery", {
                        "callback_query_id": callback_id,
                        "text": "❌ Вы пока не подписались на канал!",
                        "show_alert": True
                    })

        elif "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_id = message["from"]["id"]
            text = message.get("text", "")
            
            if text == "/start":
                if check_subscription(user_id):
                    send_welcome(chat_id, host)
                else:
                    send_subscription_prompt(chat_id, host)
                    
            elif text == "/help":
                send_message(
                    chat_id,
                    "📖 <b>Помощь</b>\n\n"
                    "/start - Открыть редактор видео\n"
                    "/help - Справка"
                )
            elif "video" in message:
                webapp_url = WEBAPP_URL or f"https://{host}"
                reply_markup = {
                    "inline_keyboard": [[{
                        "text": "🎬 Открыть редактор", 
                        "web_app": {"url": webapp_url}
                    }]]
                }
                send_message(
                    chat_id,
                    "📹 Видео нужно загрузить через Mini App.\n"
                    "Нажмите кнопку ниже:",
                    reply_markup
                )
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Upscale Video Bot is running!")
