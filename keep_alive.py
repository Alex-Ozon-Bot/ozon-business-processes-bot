import requests
import time
import threading
import os
from datetime import datetime

def aggressive_keep_alive():
    """Агрессивная стратегия поддержания активности"""
    port = int(os.getenv('PORT', 8000))
    base_url = f"http://localhost:{port}"
    
    print(f"🔄 Starting AGGRESSIVE keep-alive for port {port}")
    
    ping_count = 0
    while True:
        try:
            # Чередуем разные endpoints
            if ping_count % 3 == 0:
                # Основной health check
                response = requests.get(f"{base_url}/health", timeout=10)
                status = "HEALTH"
            elif ping_count % 3 == 1:
                # Deep ping
                response = requests.get(f"{base_url}/deep-ping", timeout=10)
                status = "DEEP_PING"
            else:
                # Home page
                response = requests.get(base_url, timeout=10)
                status = "HOME"
            
            if response.status_code == 200:
                ping_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"✅ {status} ping #{ping_count} successful at {current_time}")
            else:
                print(f"⚠️ {status} ping failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Keep-alive ping error: {e}")
            
            # Пытаемся перезапустить health server при ошибках
            try:
                restart_health_server()
            except Exception as restart_error:
                print(f"🚨 Failed to restart health server: {restart_error}")
        
        # Увеличиваем частоту пингов до каждых 30 секунд
        time.sleep(30)

def restart_health_server():
    """Перезапускает health server при необходимости"""
    print("🔄 Attempting to restart health server...")
    # Здесь можно добавить логику перезапуска
    # Например, через subprocess если нужно

def start_aggressive_keep_alive():
    """Запускает агрессивный keep-alive"""
    thread = threading.Thread(target=aggressive_keep_alive, daemon=True)
    thread.start()
    print("🔄 AGGRESSIVE keep-alive started (30s intervals)")

# Дополнительная защита от сна
def prevent_sleep():
    """Дополнительные действия для предотвращения сна"""
    while True:
        try:
            # Создаем некоторую нагрузку на CPU
            _ = [i**2 for i in range(1000)]
            
            # Периодически пишем в лог
            if int(time.time()) % 300 == 0:  # Каждые 5 минут
                print("💤 Sleep prevention active...")
                
        except Exception as e:
            print(f"❌ Sleep prevention error: {e}")
        
        time.sleep(60)

def start_sleep_prevention():
    """Запускает механизм предотвращения сна"""
    thread = threading.Thread(target=prevent_sleep, daemon=True)
    thread.start()
    print("💤 Sleep prevention started")