import os
from dotenv import load_dotenv

load_dotenv()

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в переменных окружения. Создайте файл .env с BOT_TOKEN=your_bot_token")

# Получаем ID администратора из переменных окружения
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID не установлен в переменных окружения. Создайте файл .env с ADMIN_CHAT_ID=your_chat_id")

try:
    ADMIN_CHAT_ID = int(ADMIN_CHAT_ID)
except ValueError:
    raise ValueError("❌ ADMIN_CHAT_ID должен быть числовым идентификатором")

DATABASE_NAME = 'data/processes.db'

# Создаем папку data если ее нет
if not os.path.exists('data'):
    os.makedirs('data')

print("✅ Конфигурация загружена успешно")