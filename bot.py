import requests
import time
import json
import os
from flask import Flask

# Create a Flask app for the web server
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

# Bitget API credentials
API_KEY = os.environ.get('BITGET_API_KEY')
SECRET_KEY = os.environ.get('BITGET_SECRET_KEY')
PASSPHRASE = os.environ.get('BITGET_PASSPHRASE')

# Telegram Bot credentials
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Trader to monitor
TRADER_ID = os.environ.get('TRADER_ID')

# Bitget API endpoints
BASE_URL = 'https://api.bitget.com'
COPY_TRADES_ENDPOINT = '/api/mix/v1/copy/currentOrders'

# Function to get current positions
def get_current_positions():
    timestamp = str(int(time.time() * 1000))
    
    # Create signature (simplified for now - implement proper signing method)
    signature = 'your_signature_method'
    
    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}{COPY_TRADES_ENDPOINT}", headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error fetching positions: {str(e)}")
        return {"data": []}

# Function to send message to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")
        return {}

# Start monitoring in a background thread
import threading

def monitor_trades():
    print("Starting trade monitoring...")
    known_positions = {}
    
    while True:
        try:
            current_data = get_current_positions()
            
            if 'data' in current_data:
                for position in current_data['data']:
                    position_id = position.get('orderId')
                    
                    if position_id and position_id not in known_positions:
                        known_positions[position_id] = position
                        
                        if position.get('traderId') == TRADER_ID:
                            symbol = position.get('symbol', 'Unknown')
                            side = position.get('side', 'Unknown')
                            size = position.get('size', 'Unknown')
                            price = position.get('price', 'Unknown')
                            leverage = position.get('leverage', 'Unknown')
                            
                            message = f"🟢 *New Position Opened!* 🟢\n\n" \
                                      f"Trader: {TRADER_ID}\n" \
                                      f"Symbol: {symbol}\n" \
                                      f"Action: {side}\n" \
                                      f"Size: {size}\n" \
                                      f"Price: {price}\n" \
                                      f"Leverage: {leverage}x\n\n" \
                                      f"Trade ID: `{position_id}`"
                            
                            send_result = send_telegram_message(message)
                            print(f"New position notification sent: {symbol} {side}")
            
            # Check every 30 seconds
            time.sleep(30)
            
        except Exception as e:
            print(f"Error during monitoring: {str(e)}")
            time.sleep(60)

# Start the monitoring in a background thread
monitor_thread = threading.Thread(target=monitor_trades, daemon=True)
monitor_thread.start()

# Don't run the Flask app here - let Gunicorn handle it
if __name__ == "__main__":
    # This is only for local testing
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
