import requests
import time
import json
import os
from flask import Flask

# Set up a simple web server to respond to pings
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
    
    # Create signature (this is a simplified example - you'll need to follow Bitget's signing method)
    # In a real implementation, you would sign the request according to Bitget's API documentation
    signature = 'your_signature_generation_method'
    
    headers = {
        'ACCESS-KEY': API_KEY,
        'ACCESS-SIGN': signature,
        'ACCESS-TIMESTAMP': timestamp,
        'ACCESS-PASSPHRASE': PASSPHRASE,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{BASE_URL}{COPY_TRADES_ENDPOINT}", headers=headers)
    return response.json()

# Function to send message to Telegram
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    response = requests.post(url, data=payload)
    return response.json()

# Main monitoring function
def monitor_trades():
    print("Starting trade monitoring...")
    known_positions = {}
    
    while True:
        try:
            current_data = get_current_positions()
            
            if 'data' in current_data:
                # Check for new positions
                for position in current_data['data']:
                    position_id = position.get('orderId')
                    
                    # If this is a new position we haven't seen before
                    if position_id and position_id not in known_positions:
                        known_positions[position_id] = position
                        
                        # Check if it belongs to the trader we're monitoring
                        if position.get('traderId') == TRADER_ID:
                            # Format and send message
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
            # Wait a bit longer if there was an error
            time.sleep(60)

# Main thread to run monitoring
import threading
def run_monitoring():
    monitor_trades()

# Start monitoring in a separate thread
monitoring_thread = threading.Thread(target=run_monitoring, daemon=True)
monitoring_thread.start()

# Run the Flask app for health checks
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)