import os
import time
from flask import Flask
import threading
import requests

app = Flask(__name__)

# Глобальные переменные
start_time = time.time()
restart_count = 0

class HealthMonitor:
    def __init__(self):
        self.last_ping = time.time()
        self.ping_count = 0
        self.health_status = "healthy"
    
    def record_ping(self):
        self.last_ping = time.time()
        self.ping_count += 1
        
        # Проверяем, не пора ли сделать дополнительный пинг
        if self.ping_count % 10 == 0:
            self.health_status = "very_healthy"
            print(f"🌟 Super health check #{self.ping_count}")

monitor = HealthMonitor()

@app.route('/')
def home():
    return {
        'status': 'RUNNING',
        'service': 'Telegram Bot',
        'timestamp': time.time(),
        'uptime': round(time.time() - start_time, 2)
    }

@app.route('/health')
def health():
    monitor.record_ping()
    return {
        'status': 'OK',
        'ping_count': monitor.ping_count,
        'timestamp': time.time(),
        'uptime': round(time.time() - start_time, 2),
        'health': monitor.health_status
    }

@app.route('/deep-ping')
def deep_ping():
    """Глубокий пинг с дополнительными проверками"""
    monitor.record_ping()
    
    # Выполняем самопинг для активности
    try:
        port = int(os.getenv('PORT', 8000))
        requests.get(f"http://localhost:{port}/health", timeout=5)
    except:
        pass
    
    return {
        'status': 'DEEP_PING_OK',
        'timestamp': time.time(),
        'message': 'Deep health check completed',
        'system_time': datetime.now().isoformat()
    }

@app.route('/status')
def status():
    """Расширенный статус"""
    return {
        'status': 'OPERATIONAL',
        'service': 'Ozon Processes Bot',
        'start_time': start_time,
        'current_time': time.time(),
        'uptime_seconds': round(time.time() - start_time, 2),
        'total_pings': monitor.ping_count,
        'last_ping': monitor.last_ping,
        'health_status': monitor.health_status
    }

def background_activities():
    """Фоновые активности для поддержания работы"""
    while True:
        try:
            # Периодические действия для поддержания активности
            if int(time.time()) % 300 == 0:  # Каждые 5 минут
                print("💫 Background activity: Maintaining service...")
                
            # Проверяем время без пингов
            time_since_last_ping = time.time() - monitor.last_ping
            if time_since_last_ping > 300:  # 5 минут
                print(f"⚠️ No pings for {time_since_last_ping:.0f} seconds")
                
        except Exception as e:
            print(f"❌ Background activity error: {e}")
        
        time.sleep(60)

def run_health_server():
    port = int(os.getenv('PORT', 8000))
    print(f"🚀 Health server starting on port {port}")
    print(f"📍 Endpoints:")
    print(f"   • http://0.0.0.0:{port}/health")
    print(f"   • http://0.0.0.0:{port}/status")
    print(f"   • http://0.0.0.0:{port}/deep-ping")
    
    # Запускаем фоновые активности
    bg_thread = threading.Thread(target=background_activities, daemon=True)
    bg_thread.start()
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,
        use_reloader=False
    )

if __name__ == '__main__':
    run_health_server()