import os
import asyncio
from aiogram import Bot, Dispatcher
from aiohttp import web

# ===== Настройки =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== Список пользователей для теста =====
# Замените 123456789 на свой Telegram user ID, чтобы бот прислал сообщение сразу
users = {123456789}

# ===== Тестовая функция для проверки работы =====
async def send_test_message():
    for user_id in users:
        await bot.send_message(user_id, "Бот работает! 🎉")

# ===== Фиктивный веб-сервер для Render =====
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))  # Render задаёт PORT автоматически
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ===== Главная функция =====
async def main():
    # Запускаем фиктивный веб-сервер, чтобы Render был доволен
    await start_web_server()

    # Отправляем тестовое сообщение прямо сейчас
    await send_test_message()

    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
