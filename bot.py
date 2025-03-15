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

# Add a test endpoint
@app.route('/test')
def test():
    try:
        # Test Telegram connection with more detailed logging
        telegram_status = "❌ Error"
        try:
            print(f"Testing Telegram with token: {TELEGRAM_BOT_TOKEN[:4]}...{TELEGRAM_BOT_TOKEN[-4:]}")
            print(f"Chat ID: {TELEGRAM_CHAT_ID}")
            result = send_telegram_message("🧪 *Test Message* 🧪\nThis is a test from your Bitget notification bot.")
            print(f"Telegram result: {result}")
            if result.get('ok'):
                telegram_status = "✅ Connected"
            else:
                telegram_status = f"❌ Error: {result.get('description', 'Unknown error')}"
        except Exception as e:
            telegram_status = f"❌ Error: {str(e)}"
            print(f"Telegram test exception: {str(e)}")
        
        # Test Telegram connection
        telegram_status = "❌ Error"
        try:
            result = send_telegram_message("🧪 *Test Message* 🧪\nThis is a test from your Bitget notification bot.")
            if result.get('ok'):
                telegram_status = "✅ Connected"
        except Exception as e:
            telegram_status = f"❌ Error: {str(e)[:100]}"
        
        # Create response
        response = f"""
Bot Test Results:

Bitget API: {bitget_status}
Telegram: {telegram_status}
Trader ID: {TRADER_ID or "Not set"}

Environment variables:
- BITGET_API_KEY: {"✅ Set" if API_KEY else "❌ Missing"}
- BITGET_SECRET_KEY: {"✅ Set" if SECRET_KEY else "❌ Missing"}
- BITGET_PASSPHRASE: {"✅ Set" if PASSPHRASE else "❌ Missing"}
- TELEGRAM_BOT_TOKEN: {"✅ Set" if TELEGRAM_BOT_TOKEN else "❌ Missing"}
- TELEGRAM_CHAT_ID: {"✅ Set" if TELEGRAM_CHAT_ID else "❌ Missing"}
- TRADER_ID: {"✅ Set" if TRADER_ID else "❌ Missing"}
        """
        return response
    except Exception as e:
        return f"Test failed with error: {str(e)}"

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
        print(f"Attempting to send Telegram message")
        response = requests.post(url, json=payload)  # Changed from data=payload to json=payload
        print(f"Telegram API response status: {response.status_code}")
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
