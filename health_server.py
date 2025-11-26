import os
import time
from flask import Flask
from threading import Thread
import requests

app = Flask(__name__)

class HealthMonitor:
    def __init__(self):
        self.last_ping = time.time()
        self.ping_count = 0
    
    def record_ping(self):
        self.last_ping = time.time()
        self.ping_count += 1

monitor = HealthMonitor()

@app.route('/')
def home():
    return "🤖 Telegram Bot is Running!"

@app.route('/health')
def health():
    monitor.record_ping()
    return {
        'status': 'OK',
        'timestamp': time.time(),
        'ping_count': monitor.ping_count,
        'uptime': time.time() - start_time
    }

@app.route('/deep-ping')
def deep_ping():
    """Более агрессивный пинг для поддержания активности"""
    monitor.record_ping()
    
    # Выполняем дополнительные действия для поддержания активности
    try:
        # Пингуем самого себя через другой endpoint
        requests.get(f"http://localhost:{port}/health", timeout=5)
    except:
        pass
    
    return {
        'status': 'DEEP_PING_OK',
        'timestamp': time.time(),
        'message': 'Aggressive keep-alive activated'
    }

def run_health_server():
    port = int(os.getenv('PORT', 8000))
    print(f"🚀 Health server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

def start_external_ping():
    """Запускает внешние пинги к популярным сервисам"""
    def ping_services():
        services = [
            'https://www.google.com',
            'https://api.telegram.org',
            'https://httpbin.org/get'
        ]
        
        while True:
            for service in services:
                try:
                    requests.get(service, timeout=10)
                    print(f"🌐 External ping to {service} - OK")
                except Exception as e:
                    print(f"🌐 External ping to {service} - Failed: {e}")
            
            # Пинг каждые 5 минут
            time.sleep(300)
    
    thread = Thread(target=ping_services, daemon=True)
    thread.start()
    print("🌐 External ping service started")

# Глобальные переменные
start_time = time.time()
port = int(os.getenv('PORT', 8000))

if __name__ == '__main__':
    # Запускаем внешние пинги
    start_external_ping()
    
    # Запускаем основной сервер
    run_health_server()