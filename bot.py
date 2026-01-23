import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiohttp import web

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ===== ПАМЯТЬ =====
shopping_list = []
waiting_for_items = set()
watchers = set()

# ===== КНОПКИ =====
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Пополнить запасы 🥦")],
        [KeyboardButton(text="Продовольствия хватает 🍕")],
        [KeyboardButton(text="Продовольствия хватает 🍕")]
    ],
    resize_keyboard=True
)


# ===== /start =====
@dp.message(Command("start"))
async def start(message: types.Message):
    watchers.add(message.from_user.id)
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

# ===== ОТЛОЖИТЬ =====
@dp.message(lambda m: m.text == "Отложить 🙄")
async def postpone(message: types.Message):
    await message.answer("Отложено 😌", reply_markup=main_keyboard)

# ===== ОСНОВНОЙ ТЕКСТ =====
@dp.message()
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # === режим добавления еды ===
    if user_id in waiting_for_items:
        items = [line.strip() for line in text.split("\n") if line.strip()]

        shopping_list.extend(items)
        waiting_for_items.discard(user_id)

        await message.answer("🧾 Всё записал!", reply_markup=main_keyboard)

        # уведомляем наблюдателей
        for watcher in watchers:
            if watcher != user_id:
                await bot.send_message(
                    watcher,
                    "🏰 Княжество голодает!",
                    reply_markup=main_keyboard
                )
        return

    # === удаление по номеру ===
    if text.isdigit():
        index = int(text) - 1
        if 0 <= index < len(shopping_list):
            removed = shopping_list.pop(index)
            await message.answer(f"💀 Удалено: {removed}", reply_markup=watcher_keyboard)
        else:
            await message.answer("Такого пункта нет 🤷‍♀️", reply_markup=watcher_keyboard)
        return

    await message.answer("Используй кнопки 👇", reply_markup=main_keyboard)

# ===== WEB SERVER =====
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
#z
