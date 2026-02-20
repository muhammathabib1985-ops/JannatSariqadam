from flask import Flask
from threading import Thread
import logging
import socket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlamoqda! 🤖"

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def run():
    port = find_free_port()  # Find free port automatically
    app.run(host='0.0.0.0', port=port)
    logger.info(f"Keep alive server started on port {port}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()