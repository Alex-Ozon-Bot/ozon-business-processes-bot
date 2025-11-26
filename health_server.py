import os
import time
from flask import Flask

app = Flask(__name__)

# Глобальные переменные
start_time = time.time()

@app.route('/')
def home():
    return "🤖 Telegram Bot is Running!"

@app.route('/health')
def health():
    return {
        'status': 'OK',
        'timestamp': time.time(),
        'uptime': time.time() - start_time
    }

@app.route('/deep-ping')
def deep_ping():
    return {
        'status': 'DEEP_PING_OK',
        'timestamp': time.time()
    }

def run_health_server():
    port = int(os.getenv('PORT', 8000))
    print(f"🚀 Health server starting on port {port}")
    print(f"📍 Health endpoint: http://0.0.0.0:{port}/health")
    
    # Используем простой запуск без debug режима
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,
        use_reloader=False  # Важно: отключаем reloader
    )

if __name__ == '__main__':
    run_health_server()