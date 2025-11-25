import requests
import time
import threading
import os

def keep_alive_ping():
    """Периодически отправляет запросы к боту для поддержания активности"""
    bot_url = f"https://api.telegram.org/bot{os.getenv('BOT_TOKEN')}/getMe"
    
    while True:
        try:
            response = requests.get(bot_url, timeout=10)
            if response.status_code == 200:
                print("✅ Keep-alive ping successful")
            else:
                print(f"⚠️ Keep-alive ping failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Keep-alive ping error: {e}")
        
        # Ждем 4 минуты перед следующим пингом
        time.sleep(240)

def start_keep_alive():
    """Запускает keep-alive в фоновом потоке"""
    thread = threading.Thread(target=keep_alive_ping, daemon=True)
    thread.start()
    print("🔄 Keep-alive service started")