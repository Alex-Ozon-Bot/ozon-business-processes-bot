import os

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен в переменных окружения.")

# Жестко задаем ID администратора (ваш Telegram ID)
ADMIN_CHAT_ID = 324493714
print(f"👤 ADMIN_CHAT_ID установлен: {ADMIN_CHAT_ID}")

DATABASE_NAME = 'data/processes.db'

# Создаем папку data если ее нет
if not os.path.exists('data'):
    os.makedirs('data')

print("✅ Конфигурация загружена успешно")
print(f"🤖 BOT_TOKEN: {'Установлен' if BOT_TOKEN else 'Отсутствует'}")
