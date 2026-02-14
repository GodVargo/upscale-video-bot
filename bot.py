"""
Upscaler Video Bot — Telegram-бот для апскейла видео с помощью AI
С PostgreSQL для постоянного хранения пользователей
"""
import asyncio
import logging
import os
import csv
import io
from datetime import datetime, timedelta
from dotenv import load_dotenv

import psycopg2
from psycopg2.extras import RealDictCursor

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, BufferedInputFile, FSInputFile, CallbackQuery

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://godvargo.github.io/upscale-video-webapp/")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
DATABASE_URL = os.getenv("DATABASE_URL")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_db():
    """Подключение к PostgreSQL"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def init_db():
    """Создание таблицы пользователей"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            joined TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT TRUE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("База данных инициализирована")


def add_user(user_id: int, username: str = None, first_name: str = None):
    """Добавление нового пользователя"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (id, username, first_name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            username = EXCLUDED.username,
            first_name = EXCLUDED.first_name,
            active = TRUE
    """, (user_id, username, first_name))
    conn.commit()
    cur.close()
    conn.close()


def get_all_user_ids():
    """Получение всех ID активных пользователей"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE active = TRUE")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [row['id'] for row in rows]


def mark_inactive(user_id: int):
    """Пометить пользователя как неактивного"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET active = FALSE WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_stats():
    """Получение статистики"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as total FROM users")
    total = cur.fetchone()['total']
    
    cur.execute("SELECT COUNT(*) as active FROM users WHERE active = TRUE")
    active = cur.fetchone()['active']
    
    day_ago = datetime.now() - timedelta(hours=24)
    cur.execute("SELECT COUNT(*) as new_24h FROM users WHERE joined > %s", (day_ago,))
    new_24h = cur.fetchone()['new_24h']
    
    cur.close()
    conn.close()
    
    return {"total": total, "new_24h": new_24h, "active": active}


def export_users():
    """Экспорт всех пользователей"""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, first_name, joined, active FROM users ORDER BY joined DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


async def check_subscription(user_id: int) -> tuple[bool, str]:
    """Проверка подписки. Возвращает (True/False, ошибка)."""
    if not CHANNEL_ID:
        logger.warning("CHANNEL_ID не установлен")
        return True, ""
        
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_sub = member.status in ["creator", "administrator", "member", "restricted"]
        return is_sub, ""
    except Exception as e:
        logger.error(f"Ошибка проверки подписки для {user_id}: {e}")
        return False, str(e)


@dp.callback_query(F.data == "check_subscription")
async def callback_check_subscription(callback: CallbackQuery):
    """Обработчик кнопки проверки подписки"""
    is_subscribed, error = await check_subscription(callback.from_user.id)
    
    if is_subscribed:
        await callback.message.delete()
        await cmd_start(callback.message)
    else:
        text = "❌ Вы пока не подписались на канал!"
        if error:
            # Показываем ошибку конфигурации, чтобы пользователь понял в чем дело
            text += f"\n\n⚙️ Ошибка проверки: {error}\n(Сделайте бота администратором в канале!)"
            
        await callback.answer(text, show_alert=True)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    # Проверка подписки
    is_subscribed, error = await check_subscription(message.from_user.id)
    
    if not is_subscribed:
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Подписаться", url=CHANNEL_URL or "https://t.me/")
        builder.button(text="✅ Проверить подписку", callback_data="check_subscription")
        builder.adjust(1)
        
        caption = (
            "👋 Привет!\n\n"
            "Для использования бота необходимо подписаться на наш канал:\n"
            f"<b>AI Laboratory</b>\n\n"
            "После подписки нажмите кнопку «Проверить подписку»."
        )
        
        if error:
             caption += f"\n\n⚠️ <b>System Error:</b> {error}"

        
        photo_path = "public/subscribe_banner.jpg"
        if os.path.exists(photo_path):
            photo = FSInputFile(photo_path)
            await message.answer_photo(photo, caption=caption, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(caption, reply_markup=builder.as_markup(), parse_mode="HTML")
        return

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
        users = export_users()
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Username', 'Name', 'Joined', 'Active'])
        for user in users:
            writer.writerow([
                user['id'],
                user['username'] or '',
                user['first_name'] or '',
                user['joined'],
                user['active']
            ])
        
        csv_bytes = output.getvalue().encode('utf-8')
        file = BufferedInputFile(csv_bytes, filename=f"users_{datetime.now().strftime('%Y%m%d')}.csv")
        await message.answer_document(file, caption=f"📁 База пользователей ({len(users)} записей)")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Рассылка сообщений (только для админа)"""
    if ADMIN_ID and message.from_user.id != ADMIN_ID:
        return
    
    text = message.text.replace("/broadcast", "").strip()
    
    if not text:
        await message.answer(
            "📢 <b>Рассылка</b>\n\n"
            "Использование:\n"
            "<code>/broadcast Ваше сообщение</code>",
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
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                mark_inactive(user_id)
        
        if (i + 1) % 20 == 0:
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
        "📹 Видео нужно загрузить через апскейлер.\nНажмите кнопку ниже:",
        reply_markup=builder.as_markup()
    )


async def check_bot_admin_status():
    """Проверка прав админа при запуске"""
    if not CHANNEL_ID:
        return

    try:
        bot_user = await bot.get_me()
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=bot_user.id)
        if member.status != "administrator":
            logger.critical(f"⚠️ БОТ НЕ ЯВЛЯЕТСЯ АДМИНИСТРАТОРОМ В КАНАЛЕ {CHANNEL_ID}! Проверка подписки работать не будет.")
        else:
            logger.info(f"✅ Бот успешно проверил права админа в канале {CHANNEL_ID}")
    except Exception as e:
        logger.critical(f"⚠️ Ошибка проверки прав бота в канале {CHANNEL_ID}: {e}. Убедитесь, что ID правильный и бот добавлен в канал.")

async def main():
    """Запуск бота"""
    init_db()
    
    # Проверка прав перед запуском
    await check_bot_admin_status()
    
    logger.info("🚀 Запуск Upscaler Video Bot...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
