Bitget Copy Trading Notification Bot
A simple bot that monitors your Bitget copy trades and sends notifications to Telegram when the trader you follow opens or closes positions.
Features

Real-time notifications when your followed trader opens a new position
Detailed information about each trade (symbol, direction, size, price, leverage)
Simple web interface to check bot status
Test endpoint to verify connections
Free deployment options

Setup Guide
Prerequisites

Bitget account with API access
Telegram account
GitHub account (for deployment)

Step 1: Create a Telegram Bot

Open Telegram and search for @BotFather
Send the command /newbot
Follow instructions to name your bot
Save the API token provided (will look like 123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ)
Start a conversation with your new bot by searching for it and pressing Start

Step 2: Get Your Telegram Chat ID

Send a message to your bot
Visit https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
Look for a number in the format "chat":{"id":123456789}
Copy this number as your TELEGRAM_CHAT_ID

Step 3: Create Bitget API Keys

Log in to your Bitget account
Go to "API Management" in your account settings
Click "Create API Key"
Set the following permissions:

Futures → Orders (read)
Futures → Holdings (read)
Copy trading → Trade (read)


Complete security verification if required
Save your API Key, Secret Key, and Passphrase securely

Step 4: Deploy on Render.com (Free)

Create a GitHub repository with these files:

bot.py
pythonKopierenimport requests
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
        # Initialize status variables
        bitget_status = "❌ Error"
        telegram_status = "❌ Error"
        
        # Test Bitget API connection
        try:
            positions = get_current_positions()
            if 'data' in positions:
                bitget_status = "✅ Connected"
        except Exception as e:
            bitget_status = f"❌ Error: {str(e)[:100]}"
        
        # Test Telegram connection
        try:
            result = send_telegram_message("🧪 *Test Message* 🧪\nThis is a test from your Bitget notification bot.")
            if result.get('ok'):
                telegram_status = "✅ Connected"
            else:
                telegram_status = f"❌ Error: {result.get('description', 'Unknown error')}"
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
    
    # Create signature (implement proper signing method for production)
    # For Bitget API documentation on signing: https://bitgetlimited.github.io/apidoc/en/mix/#signature
    import hmac
    import base64
    import hashlib
    
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
import threading

def monitor_trades():
    print("Starting trade monitoring...")
    known_positions = {}
    closed_positions = set()
    
    while True:
        try:
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
            
            # Clean up old closed positions occasionally
            if len(closed_positions) > 100:
                closed_positions = set(list(closed_positions)[-50:])
            
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
requirements.txt
KopierenFlask==2.0.1
Werkzeug==2.0.2
requests==2.28.1
gunicorn==20.1.0
Procfile
Kopierenweb: gunicorn bot:app

Sign up for Render.com (free tier)
Create a new Web Service
Connect your GitHub repository
Set up the service:

Name: bitget-notification-bot
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn bot:app


Add Environment Variables:

BITGET_API_KEY: Your Bitget API key
BITGET_SECRET_KEY: Your Bitget Secret key
BITGET_PASSPHRASE: Your Bitget API passphrase
TELEGRAM_BOT_TOKEN: Your Telegram bot token
TELEGRAM_CHAT_ID: Your Telegram chat ID
TRADER_ID: The ID of the trader you want to follow


Deploy the service

Step 5: Set Up UptimeRobot to Keep the Bot Running

Sign up for UptimeRobot.com (free)
Add a new monitor
Select "HTTP(s)"
Name it "Bitget Bot"
Enter your Render URL
Set check interval to 5 minutes
Save the monitor

Usage

Visit your bot URL to check if it's running
Visit your-bot-url/test to test API connections
Your bot will automatically send notifications to Telegram when your followed trader opens or closes positions

Troubleshooting

If Telegram notifications aren't working, verify your bot token and chat ID
If you're monitoring a group chat, make sure you have the correct chat ID (may start with a minus sign)
For supergroups, the chat ID typically starts with -100 followed by numbers
Check the /test endpoint for specific error messages

Customization
You can modify the bot.py file to:

Change notification message format
Adjust monitoring frequency (default is 30 seconds)
Add more detailed trade information
Track multiple traders simultaneously

Security Notes

Your API keys are stored as environment variables and not exposed in the code
The Bitget API permissions are read-only, so the bot cannot make trades
Always use read-only API permissions when possible

Support
For issues or questions, check the Bitget API documentation or Telegram Bot API documentation.
