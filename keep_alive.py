import requests
import time
import threading
import os
from datetime import datetime

def keep_alive_ping():
    """Простой и надежный keep-alive"""
    port = int(os.getenv('PORT', 8000))
    base_url = f"http://localhost:{port}"
    
    print(f"🔄 Simple keep-alive starting for port {port}")
    
    ping_count = 0
    while True:
        try:
            response = requests.get(f"{base_url}/health", timeout=10)
            if response.status_code == 200:
                ping_count += 1
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"✅ Keep-alive ping #{ping_count} at {current_time}")
            else:
                print(f"⚠️ Keep-alive ping failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Keep-alive ping error: {e}")
        
        # Увеличиваем интервал до 2 минут
        time.sleep(120)

def start_keep_alive():
    """Запускает keep-alive"""
    thread = threading.Thread(target=keep_alive_ping, daemon=True)
    thread.start()
    print("🔄 Keep-alive started (2 minute intervals)")