"""
Upscaler Video Bot — Telegram-бот для апскейла видео с помощью AI
С функциями статистики и рассылки
"""
import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8560064127:AAESCPlqu9_ht76zTNZ6V8Z1v9SyNyvonHQ")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://upscale-video-webapp.vercel.app")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Твой Telegram ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Файл для хранения пользователей
USERS_FILE = "users.json"

def load_users():
    """Загрузка пользователей из файла"""
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": {}}

def save_users(data):
    """Сохранение пользователей в файл"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def add_user(user_id: int, username: str = None, first_name: str = None):
    """Добавление нового пользователя"""
    data = load_users()
    user_id_str = str(user_id)
    
    if user_id_str not in data["users"]:
        data["users"][user_id_str] = {
            "id": user_id,
            "username": username,
            "first_name": first_name,
            "joined": datetime.now().isoformat(),
            "active": True
        }
        save_users(data)
        logger.info(f"Новый пользователь: {user_id} (@{username})")
        return True  # Новый пользователь
    return False  # Уже существует

def get_all_user_ids():
    """Получение всех ID активных пользователей"""
    data = load_users()
    return [int(uid) for uid, info in data["users"].items() if info.get("active", True)]

def get_stats():
    """Получение статистики"""
    data = load_users()
    now = datetime.now()
    day_ago = now - timedelta(hours=24)
    
    total = len(data["users"])
    active = len([u for u in data["users"].values() if u.get("active", True)])
    
    # Новые за 24 часа
    new_24h = 0
    for user in data["users"].values():
        try:
            joined = datetime.fromisoformat(user.get("joined", "2000-01-01"))
            if joined > day_ago:
                new_24h += 1
        except:
            pass
    
    return {
        "total": total,
        "new_24h": new_24h,
        "active": active
    }


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Сохраняем пользователя
    add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎬 Улучшить видео",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "🎬 <b>Upscaler Video</b>\n\n"
        "Telegram-бот для апскейла и улучшения видео с помощью искусственного интеллекта.\n\n"
        "📌 <b>Возможности:</b>\n"
        "• Апскейл видео\n"
        "• Повышение чёткости\n"
        "• Улучшение деталей\n"
        "• Быстро и прямо в Telegram\n\n"
        "Просто нажмите кнопку ниже — остальное сделает ИИ.",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 <b>Помощь</b>\n\n"
        "Бот увеличивает разрешение, улучшает детализацию и делает видео "
        "более чётким — идеально для старых роликов, соцсетей и контента, "
        "где важно качество.\n\n"
        "<b>Команды:</b>\n"
        "/start — Открыть апскейлер\n"
        "/help — Справка",
        parse_mode="HTML"
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика (только для админа)"""
    if ADMIN_ID and message.from_user.id != ADMIN_ID:
        return
    
    stats = get_stats()
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего в базе: <b>{stats['total']}</b>\n"
        f"📈 Новых за 24 часа: <b>{stats['new_24h']}</b>\n"
        f"✅ Активных: <b>{stats['active']}</b>",
        parse_mode="HTML"
    )


@dp.message(Command("export"))
async def cmd_export(message: Message):
    """Экспорт базы пользователей (только для админа)"""
    if ADMIN_ID and message.from_user.id != ADMIN_ID:
        return
    
    try:
        if os.path.exists(USERS_FILE):
            file = FSInputFile(USERS_FILE, filename="users_database.json")
            await message.answer_document(file, caption="📁 База пользователей")
        else:
            await message.answer("❌ База пользователей пуста")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Рассылка сообщений (только для админа)"""
    if ADMIN_ID and message.from_user.id != ADMIN_ID:
        return
    
    # Получаем текст после команды
    text = message.text.replace("/broadcast", "").strip()
    
    if not text:
        await message.answer(
            "📢 <b>Рассылка</b>\n\n"
            "Использование:\n"
            "<code>/broadcast Ваше сообщение</code>\n\n"
            "Сообщение будет отправлено всем подписчикам.",
            parse_mode="HTML"
        )
        return
    
    user_ids = get_all_user_ids()
    sent = 0
    failed = 0
    
    status_msg = await message.answer(f"📤 Рассылка... 0/{len(user_ids)}")
    
    for i, user_id in enumerate(user_ids):
        try:
            await bot.send_message(user_id, text, parse_mode="HTML")
            sent += 1
        except Exception as e:
            failed += 1
            # Помечаем как неактивного если заблокировал
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                data = load_users()
                if str(user_id) in data["users"]:
                    data["users"][str(user_id)]["active"] = False
                    save_users(data)
        
        if (i + 1) % 10 == 0:
            await status_msg.edit_text(f"📤 Рассылка... {i+1}/{len(user_ids)}")
        
        await asyncio.sleep(0.05)
    
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📨 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}",
        parse_mode="HTML"
    )


@dp.message(F.video)
async def handle_video(message: Message):
    """Обработчик видео"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎬 Открыть апскейлер",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "📹 Видео нужно загрузить через апскейлер.\n"
        "Нажмите кнопку ниже:",
        reply_markup=builder.as_markup()
    )


async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск Upscaler Video Bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
