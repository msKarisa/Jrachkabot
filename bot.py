import os
import asyncio
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = pytz.timezone("Europe/Zurich")  # можно поменять при желании

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== ПАМЯТЬ =====
shopping_list = []
waiting_for_items = set()

USERS_FILE = "users.txt"

# ===== РАБОТА С ПОЛЬЗОВАТЕЛЯМИ =====
def save_user(user_id: int):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r+") as f:
        users = f.read().splitlines()
        if str(user_id) not in users:
            f.write(str(user_id) + "\n")


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return [int(u) for u in f.read().splitlines()]

# ===== КНОПКИ =====
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пополнить запасы 🥦")],
        [KeyboardButton(text="Посмотреть список жрачки 🍔")],
        [KeyboardButton(text="Продовольствия хватает 🍕")]
    ],
    resize_keyboard=True
)

# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    save_user(message.from_user.id)
    await message.answer(
        "🏰 Я бот-харчевник\nПополнить запасы харчевни?",
        reply_markup=main_keyboard
    )

# ===== ПОПОЛНИТЬ =====
@dp.message(lambda m: m.text == "Пополнить запасы 🥦")
async def add_items(message: types.Message):
    waiting_for_items.add(message.from_user.id)
    await message.answer(
        "Напиши продукты.\n"
        "Можно списком — каждый с новой строки 📝"
    )

# ===== ХВАТАЕТ =====
@dp.message(lambda m: m.text == "Продовольствия хватает 🍕")
async def enough_food(message: types.Message):
    waiting_for_items.discard(message.from_user.id)
    await message.answer("Хорошо 👌", reply_markup=main_keyboard)

# ===== ПРОСМОТР СПИСКА =====
@dp.message(lambda m: m.text == "Посмотреть список жрачки 🍔")
async def show_list(message: types.Message):
    if not shopping_list:
        await message.answer("Харчевня пуста 🍽️", reply_markup=main_keyboard)
        return

    text = "🏰 Княжество голодает!\n\n"
    for i, item in enumerate(shopping_list, 1):
        text += f"{i}. {item}\n"

    await message.answer(
        text + "\nНапиши номер, чтобы принять участь 💀",
        reply_markup=main_keyboard
    )

# ===== ТЕКСТ =====
@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # добавление еды
    if user_id in waiting_for_items:
        items = [line.strip() for line in text.split("\n") if line.strip()]
        shopping_list.extend(items)
        waiting_for_items.discard(user_id)

        await message.answer("🧾 Всё записал!", reply_markup=main_keyboard)

        for uid in load_users():
            if uid != user_id:
                await bot.send_message(
                    uid,
                    "🏰 Княжество голодает!",
                    reply_markup=main_keyboard
                )
        return

    # удаление по номеру
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(shopping_list):
            removed = shopping_list.pop(index)
            await message.answer(f"💀 Удалено: {removed}", reply_markup=main_keyboard)
        else:
            await message.answer("Такого пункта нет 🤷‍♀️", reply_markup=main_keyboard)
        return

    await message.answer("Используй кнопки 👇", reply_markup=main_keyboard)

# ===== ПЛАНИРОВЩИК =====
scheduler = AsyncIOScheduler(timezone=TIMEZONE)

async def daily_reminder():
    now = datetime.now(TIMEZONE)
    if now.weekday() < 5:  # 0–4 = ПН–ПТ
        for user_id in load_users():
            await bot.send_message(
                user_id,
                "Пополнить запасы харчевни? 🧌",
reply_markup=main_keyboard
            )

def clear_shopping_list():
    shopping_list.clear()

# ===== WEB SERVER (Render) =====
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

    scheduler.add_job(daily_reminder, "cron", hour=17, minute=0)
    scheduler.add_job(clear_shopping_list, "cron", hour=0, minute=5)
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
