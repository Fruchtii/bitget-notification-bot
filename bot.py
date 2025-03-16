import requests
import time
import json
import os
from flask import Flask
import hmac
import base64
import hashlib
import threading

# Create a Flask app for the web server
app = Flask(__name__)

@app.route('/')
def home():
    return "Trade Notification Bot is running!"

# Add a test endpoint
@app.route('/test')
def test():
    try:
        # Initialize status variables
        api_status = "❌ Error"
        telegram_status = "❌ Error"
        
        # Test API connection
        try:
            positions = get_current_positions()
            if 'data' in positions:
                api_status = "✅ Connected"
        except Exception as e:
            api_status = f"❌ Error: {str(e)[:100]}"
        
        # Test Telegram connection
        try:
            result = send_telegram_message("🧪 *Test Message* 🧪\nThis is a test from your Trade Notification Bot.")
            if result.get('ok'):
                telegram_status = "✅ Connected"
            else:
                telegram_status = f"❌ Error: {result.get('description', 'Unknown error')}"
        except Exception as e:
            telegram_status = f"❌ Error: {str(e)[:100]}"
        
        # Create response
        response = f"""
Bot Test Results:

API: {api_status}
Telegram: {telegram_status}
Trader ID: {TRADER_ID or "Not set"}

Environment variables:
- API_KEY: {"✅ Set" if API_KEY else "❌ Missing"}
- SECRET_KEY: {"✅ Set" if SECRET_KEY else "❌ Missing"}
- PASSPHRASE: {"✅ Set" if PASSPHRASE else "❌ Missing"}
- TELEGRAM_BOT_TOKEN: {"✅ Set" if TELEGRAM_BOT_TOKEN else "❌ Missing"}
- TELEGRAM_CHAT_ID: {"✅ Set" if TELEGRAM_CHAT_ID else "❌ Missing"}
- TRADER_ID: {"✅ Set" if TRADER_ID else "❌ Missing"}
        """
        return response
    except Exception as e:
        return f"Test failed with error: {str(e)}"

# API credentials
API_KEY = os.environ.get('BITGET_API_KEY')
SECRET_KEY = os.environ.get('BITGET_SECRET_KEY')
PASSPHRASE = os.environ.get('BITGET_PASSPHRASE')

# Telegram Bot credentials
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Trader to monitor
TRADER_ID = os.environ.get('TRADER_ID')

# API endpoints
BASE_URL = 'https://api.bitget.com'
COPY_TRADES_ENDPOINT = '/api/mix/v1/copy/currentOrders'
HISTORY_ENDPOINT = '/api/mix/v1/copy/historyOrders'

# Function to get current positions
def get_current_positions():
    timestamp = str(int(time.time() * 1000))
    
    # Create signature
    message = timestamp + 'GET' + COPY_TRADES_ENDPOINT
    signature = base64.b64encode(hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    
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

# Function to get position history
def get_history_positions():
    timestamp = str(int(time.time() * 1000))
    
    # Create signature
    message = timestamp + 'GET' + HISTORY_ENDPOINT
    signature = base64.b64encode(hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()).decode('utf-8')
    
    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{BASE_URL}{HISTORY_ENDPOINT}", headers=headers)
        return response.json()
    except Exception as e:
        print(f"Error fetching history: {str(e)}")
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
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")
        return {}

# Start monitoring in a background thread
def monitor_trades():
    print("Starting trade monitoring...")
    known_positions = {}
    closed_positions = set()
    
    # Initial check to populate known positions
    try:
        initial_data = get_current_positions()
        if 'data' in initial_data:
            for position in initial_data['data']:
                position_id = position.get('orderId')
                if position_id:
                    known_positions[position_id] = position
            print(f"Loaded {len(known_positions)} existing positions")
    except Exception as e:
        print(f"Error during initial loading: {str(e)}")
    
    while True:
        try:
            # Get current open positions
            current_data = get_current_positions()
            current_position_ids = set()
            
            # Check for new positions
            if 'data' in current_data:
                for position in current_data['data']:
                    position_id = position.get('orderId')
                    if position_id:
                        current_position_ids.add(position_id)
                    
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
            
            # Check for closed positions
            for position_id, position in list(known_positions.items()):
                if position_id not in current_position_ids and position_id not in closed_positions:
                    closed_positions.add(position_id)
                    
                    if position.get('traderId') == TRADER_ID:
                        symbol = position.get('symbol', 'Unknown')
                        side = position.get('side', 'Unknown')
                        size = position.get('size', 'Unknown')
                        
                        message = f"🔴 *Position Closed!* 🔴\n\n" \
                                  f"Trader: {TRADER_ID}\n" \
                                  f"Symbol: {symbol}\n" \
                                  f"Action: {side} (closed)\n" \
                                  f"Size: {size}\n" \
                                  f"Trade ID: `{position_id}`"
                        
                        send_result = send_telegram_message(message)
                        print(f"Position closed notification sent: {symbol} {side}")
            
            # Occasionally check history for any missed trades
            if int(time.time()) % 300 < 10:  # Every ~5 minutes
                try:
                    history_data = get_history_positions()
                    if 'data' in history_data:
                        for hist_position in history_data['data'][:20]:  # Check recent history
                            position_id = hist_position.get('orderId')
                            # Process any positions we might have missed
                            if position_id and position_id not in known_positions and position_id not in closed_positions:
                                closed_positions.add(position_id)
                                if hist_position.get('traderId') == TRADER_ID:
                                    symbol = hist_position.get('symbol', 'Unknown')
                                    side = hist_position.get('side', 'Unknown')
                                    size = hist_position.get('size', 'Unknown')
                                    profit = hist_position.get('profit', 'Unknown')
                                    
                                    message = f"📊 *Missed Trade Detected!* 📊\n\n" \
                                              f"Trader: {TRADER_ID}\n" \
                                              f"Symbol: {symbol}\n" \
                                              f"Action: {side}\n" \
                                              f"Size: {size}\n" \
                                              f"Profit: {profit}\n" \
                                              f"Trade ID: `{position_id}`"
                                    
                                    send_result = send_telegram_message(message)
                                    print(f"Missed trade notification sent: {symbol} {side}")
                except Exception as e:
                    print(f"Error checking history: {str(e)}")
            
            # Clean up old closed positions occasionally
            if len(closed_positions) > 100:
                closed_positions = set(list(closed_positions)[-50:])
            
            # Check every 10 seconds
            time.sleep(10)
            
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
