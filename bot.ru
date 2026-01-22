import asyncio
import os
from datetime import datetime
import pytz

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

# ========== Настройки ==========
BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = "Europe/Zurich"
bot = Bot(BOT_TOKEN)
dp = Dispatcher()
tz = pytz.timezone(TIMEZONE)

wishlist: list[str] = []
users: set[int] = set()
today_authors: set[int] = set()
awaiting_input: set[int] = set()

# ========== Кнопки ==========
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить запасы🥦", callback_data="add")],
        [InlineKeyboardButton(text="Продовольствия хватает🍕", callback_data="enough")]
    ])

def shopper_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="посмотреть список жрачки🍔", callback_data="view")]
    ])

def list_item_menu(index: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="принять участь💀", callback_data=f"delete_{index}")],
        [InlineKeyboardButton(text="отложить🙄", callback_data="postpone")]
    ])

# ========== Логика ==========
async def send_daily_menu():
    if datetime.now(tz).weekday() < 5:
        for user_id in users:
            await bot.send_message(user_id, "Пополнить запасы харчевни?🧌", reply_markup=main_menu())

async def reset_day():
    wishlist.clear()
    today_authors.clear()
    awaiting_input.clear()

# ========== Хэндлеры ==========
@dp.message(CommandStart())
async def start(message: Message):
    users.add(message.from_user.id)
    await message.answer("Я бот-харчевник 🧌")

@dp.callback_query(F.data == "add")
async def add_food(callback: CallbackQuery):
    users.add(callback.from_user.id)
    awaiting_input.add(callback.from_user.id)
    await callback.message.answer("Напиши, что нужно купить 🥕")
    await callback.answer()

@dp.message()
async def collect_food(message: Message):
    user_id = message.from_user.id
    users.add(user_id)

    if user_id not in awaiting_input:
        return

    wishlist.append(message.text)
    awaiting_input.remove(user_id)
    today_authors.add(user_id)
    await message.answer("Записал ✍️")

    for uid in users:
        if uid != user_id:
            await bot.send_message(uid, "Княжество голодает!🏰", reply_markup=shopper_menu())

@dp.callback_query(F.data == "enough")
async def enough(callback: CallbackQuery):
    users.add(callback.from_user.id)
    await callback.answer("Принято 🍕")

@dp.callback_query(F.data == "view")
async def view_list(callback: CallbackQuery):
    if not wishlist:
        await callback.message.answer("Список пуст. Народ пока жив 😌")
        await callback.answer()
        return

    text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(wishlist)])
    await callback.message.answer(text)
    for i, item in enumerate(wishlist):
        await callback.message.answer(f"❌ {item}", reply_markup=list_item_menu(i))
    await callback.answer()

@dp.callback_query(F.data.startswith("delete_"))
async def delete_item(callback: CallbackQuery):
    index = int(callback.data.split("_")[1])
    if 0 <= index < len(wishlist):
        del wishlist[index]
        await callback.message.answer("Вычеркнуто 💀")
    await callback.answer()

@dp.callback_query(F.data == "postpone")
async def postpone(callback: CallbackQuery):
    await callback.message.answer("Пополнить запасы харчевни?🧌", reply_markup=main_menu())
    await callback.answer()

# ========== Фиктивный HTTP-сервер для Render ==========
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

# ========== Запуск ==========
async def main():
    # запускаем фиктивный веб-сервер, чтобы Render был доволен
    await start_web_server()

    # scheduler для ежедневной рассылки
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(send_daily_menu, "cron", hour=17, minute=0)
    scheduler.add_job(reset_day, "cron", hour=0, minute=0)
    scheduler.start()

    # ===== ТЕСТОВЫЙ ВЫЗОВ, чтобы проверить работу прямо сейчас =====
    await send_daily_menu()
    # =========================================

    # запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
