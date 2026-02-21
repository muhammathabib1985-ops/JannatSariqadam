from flask import Flask
from threading import Thread
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlamoqda! 🤖"

@app.route('/health')
def health():
    return "OK", 200

def run():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
    logger.info(f"Keep alive server started on port {port}")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()