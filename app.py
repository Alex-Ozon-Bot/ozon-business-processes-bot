import os
import threading
import time
from flask import Flask, jsonify
import subprocess
import sys

app = Flask(__name__)
start_time = time.time()

def run_bot():
    """Запускает бота в отдельном процессе"""
    print("🤖 Запуск Telegram бота...")
    # Запускаем bot.py как отдельный процесс
    subprocess.Popen([sys.executable, "bot.py"])

@app.route('/')
def home():
    return f"Ozon Bot запущен! Время работы: {time.time() - start_time:.0f} сек"

@app.route('/health')
def health():
    return 'OK', 200

@app.route('/ping')
def ping():
    return 'OK', 200

if __name__ == '__main__':
    # Запускаем бота в фоновом процессе
    bot_process = threading.Thread(target=run_bot, daemon=True)
    bot_process.start()
    
    # Получаем порт из переменной окружения (Render сам назначает)
    port = int(os.environ.get('PORT', 10000))
    
    print(f"🚀 Запуск Flask сервера на порту {port}")
    print(f"📍 Доступные эндпоинты:")
    print(f"   • / - Главная страница")
    print(f"   • /health - Проверка здоровья")
    print(f"   • /ping - Лёгкий пинг")
    
    # ОБЯЗАТЕЛЬНО используйте 0.0.0.0 для Render!
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)