"""
Upscale Video Bot - Telegram бот для улучшения видео через Mini App
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN", "8560064127:AAESCPlqu9_ht76zTNZ6V8Z1v9SyNyvonHQ")

# URL Mini App (нужно будет захостить)
# Для тестирования можно использовать ngrok или GitHub Pages
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://upscale-video-webapp.vercel.app")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    builder = InlineKeyboardBuilder()
    
    # Кнопка для открытия Mini App
    builder.button(
        text="🎬 Улучшить видео",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "👋 <b>Добро пожаловать в Upscale Video Bot!</b>\n\n"
        "🎥 Этот бот улучшает качество видео с помощью AI.\n\n"
        "📱 <b>Как использовать:</b>\n"
        "1. Нажмите кнопку «Улучшить видео» ниже\n"
        "2. Загрузите ваше видео в открывшемся окне\n"
        "3. Выберите параметры улучшения\n"
        "4. Дождитесь обработки и скачайте результат\n\n"
        "⚡ Обработка происходит прямо в вашем браузере - это бесплатно и безопасно!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    await message.answer(
        "📖 <b>Помощь по боту</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку\n\n"
        "<b>Как это работает:</b>\n"
        "Бот использует технологию AI-апскейлинга на основе WebGPU. "
        "Видео обрабатывается прямо в вашем браузере, "
        "поэтому ваши файлы никуда не отправляются.\n\n"
        "<b>Поддерживаемые форматы:</b>\n"
        "MP4, WebM, MOV и другие популярные форматы\n\n"
        "<b>Рекомендации:</b>\n"
        "• Используйте на компьютере для лучшей производительности\n"
        "• Небольшие видео обрабатываются быстрее\n"
        "• Требуется современный браузер с поддержкой WebGPU",
        parse_mode="HTML"
    )


@dp.message(F.video)
async def handle_video(message: Message):
    """Обработчик видео - предлагаем открыть Mini App"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎬 Открыть редактор",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "📹 Вижу, вы отправили видео!\n\n"
        "К сожалению, прямая обработка видео через чат невозможна, "
        "так как апскейлинг выполняется в вашем браузере.\n\n"
        "👇 <b>Нажмите кнопку ниже</b>, чтобы открыть редактор и загрузить видео там:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


async def main():
    """Запуск бота"""
    logger.info("🚀 Запуск Upscale Video Bot...")
    
    # Удаляем вебхук (если был установлен)
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
