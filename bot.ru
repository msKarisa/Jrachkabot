import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== Команда /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Бот работает! 🧌")

# ===== Фиктивный веб-сервер для Render =====
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# ===== Главная функция =====
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if name == "__main__":
    asyncio.run(main())
