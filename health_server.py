import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import time

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            print(f"✅ Health check received at {time.strftime('%H:%M:%S')}")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Отключаем стандартное логирование
        pass

def run_health_server():
    port = int(os.getenv('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"🚀 Health server starting on port {port}")
    print(f"📍 Access via: http://0.0.0.0:{port}/health")
    server.serve_forever()

if __name__ == '__main__':
    run_health_server()