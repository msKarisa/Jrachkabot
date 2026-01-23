import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== ПАМЯТЬ БОТА =====
shopping_list = []
waiting_for_items = set()

# ===== КНОПКИ =====
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пополнить запасы 🥦")],
        [KeyboardButton(text="Продовольствия хватает 🍕")]
    ],
    resize_keyboard=True
)

# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Пополнить запасы харчевни? 🧌",
        reply_markup=main_keyboard
    )

# ===== НАЖАЛИ «ПОПОЛНИТЬ ЗАПАСЫ» =====
@dp.message(lambda m: m.text == "Пополнить запасы 🥦")
async def add_items(message: types.Message):
    waiting_for_items.add(message.from_user.id)
    await message.answer("Пиши, что нужно купить 📝")

# ===== НАЖАЛИ «ХВАТАЕТ» =====
@dp.message(lambda m: m.text == "Продовольствия хватает 🍕")
async def enough_food(message: types.Message):
    await message.answer(
        "Хорошо, напомню позже 🧌",
        reply_markup=main_keyboard
    )

# ===== ПРИНИМАЕМ ТЕКСТ =====
@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id

    if user_id in waiting_for_items:
        shopping_list.append(message.text)
        await message.answer("Записал 🧾")
    else:
        await message.answer("Выбери действие кнопкой 👇", reply_markup=main_keyboard)

# ===== ФИКТИВНЫЙ СЕРВЕР ДЛЯ RENDER =====
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

# ===== ЗАПУСК =====
async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
