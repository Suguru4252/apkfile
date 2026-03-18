import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

# 🔑 ВСТАВЬ СВОЙ ТОКЕН
TOKEN = "8698388173:AAFrWmLuN91hIWHmy-9l7JLhmQX46fiJdbI"

# 🌐 ССЫЛКА НА ТВОЮ ИГРУ (GitHub Pages)
WEBAPP_URL = "https://suguru4252.github.io/clicker-game/"

# Включаем логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Команда /start
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    # Создаем клавиатуру с кнопкой Web App
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(
                text="🎮 ИГРАТЬ В IMPERIA CLICKER",
                web_app=types.WebAppInfo(url=WEBAPP_URL)
            )]
        ]
    )
    
    # Отправляем приветствие с кнопкой
    await message.answer(
        "👋 **Добро пожаловать в IMPERIA CLICKER!**\n\n"
        "💰 Зарабатывай деньги кликами\n"
        "📈 Инвестируй в бизнес и крипту\n"
        "🚀 Запускай ракеты в космос\n"
        "🏠 Покупай дома и острова\n"
        "🏆 Соревнуйся в ТОП-100\n\n"
        "Нажми кнопку ниже, чтобы начать игру!",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Запуск бота
async def main():
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
