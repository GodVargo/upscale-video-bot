"""
Upscaler Video Bot — Telegram-бот для апскейла видео с помощью AI
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8560064127:AAESCPlqu9_ht76zTNZ6V8Z1v9SyNyvonHQ")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://upscale-video-webapp.vercel.app")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
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
        "/help — Справка\n\n"
        "<b>Рекомендации:</b>\n"
        "• Используйте Chrome или Edge\n"
        "• На ПК обработка быстрее\n"
        "• Видео до 100MB",
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
