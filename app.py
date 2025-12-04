import os
import threading
import subprocess
import sys
import time
from flask import Flask, jsonify
from waitress import serve

app = Flask(__name__)

# Импортируем бота
from bot import run_bot_single, init_database, create_application
import asyncio

# Глобальные переменные для мониторинга
start_time = time.time()
bot_status = "starting"

def run_bot_in_thread():
    """Запускает бота в отдельном потоке"""
    global bot_status
    try:
        print("🤖 Запуск Telegram бота в отдельном потоке...")
        bot_status = "running"
        
        # Создаем новую event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        application = create_application()
        
        async def run():
            await application.initialize()
            await application.start()
            await application.updater.start_polling()
            print("✅ Bot is running and polling...")
            while True:
                await asyncio.sleep(1)
        
        loop.run_until_complete(run())
    except Exception as e:
        bot_status = f"error: {str(e)}"
        print(f"❌ Ошибка в боте: {e}")
        # Перезапуск через 30 секунд
        time.sleep(30)
        run_bot_in_thread()

@app.route('/')
def home():
    return jsonify({
        'status': 'OK',
        'service': 'Ozon Business Processes Bot',
        'bot_status': bot_status,
        'uptime': round(time.time() - start_time, 2),
        'version': '2.0'
    })

@app.route('/health')
def health():
    """Эндпоинт для мониторинга"""
    return jsonify({
        'status': 'OK',
        'bot': bot_status,
        'timestamp': time.time()
    })

@app.route('/ping')
def ping():
    """Лёгкий пинг для UptimeRobot"""
    return jsonify({
        'status': 'OK',
        'service': 'Ozon Bot'
    })

def start_bot_thread():
    """Запускает бота в отдельном потоке"""
    # Инициализируем базу данных
    try:
        init_database()
        print("✅ База данных инициализирована")
    except Exception as e:
        print(f"⚠️ Ошибка инициализации БД: {e}")
    
    # Даем время Flask запуститься
    time.sleep(5)
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
    bot_thread.start()
    print("🤖 Поток бота запущен")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 10000))
    
    # Запускаем бота в отдельном потоке
    start_bot_thread()
    
    print(f"🚀 Запуск веб-сервера на порту {port}")
    print(f"📍 Доступные эндпоинты:")
    print(f"   • http://0.0.0.0:{port}/ - Главная страница")
    print(f"   • http://0.0.0.0:{port}/health - Проверка здоровья")
    print(f"   • http://0.0.0.0:{port}/ping - Лёгкий пинг")
    
    # Используем Waitress для продакшена
    serve(app, host='0.0.0.0', port=port)