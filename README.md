# Bitget Copy Trading Notification Bot

A simple bot that monitors your Bitget copy trades and sends notifications to Telegram when the trader you follow opens or closes positions.

## Features

- Real-time notifications when your followed trader opens a new position
- Detailed information about each trade (symbol, direction, size, price, leverage)
- Simple web interface to check bot status
- Test endpoint to verify connections
- Free deployment options

## Setup Guide

### Prerequisites

- Bitget account with API access
- Telegram account
- GitHub account (for deployment)

### Step 1: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send the command `/newbot`
3. Follow instructions to name your bot
4. Save the API token provided (will look like `123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ`)
5. Start a conversation with your new bot by searching for it and pressing Start

### Step 2: Get Your Telegram Chat ID

1. Send a message to your bot
2. Visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for a number in the format `"chat":{"id":123456789}`
4. Copy this number as your TELEGRAM_CHAT_ID

### Step 3: Create Bitget API Keys

1. Log in to your Bitget account
2. Go to "API Management" in your account settings
3. Click "Create API Key"
4. Set the following permissions:
   - Futures → Orders (read)
   - Futures → Holdings (read)
   - Copy trading → Trade (read)
5. Complete security verification if required
6. Save your API Key, Secret Key, and Passphrase securely

### Step 4: Deploy on Render.com (Free)

1. Fork or clone this repository
2. Sign up for [Render.com](https://render.com) (free tier)
3. Create a new Web Service
4. Connect your GitHub repository
5. Set up the service:
   - Name: bitget-notification-bot
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn bot:app`
6. Add Environment Variables:
   - BITGET_API_KEY: Your Bitget API key
   - BITGET_SECRET_KEY: Your Bitget Secret key
   - BITGET_PASSPHRASE: Your Bitget API passphrase
   - TELEGRAM_BOT_TOKEN: Your Telegram bot token
   - TELEGRAM_CHAT_ID: Your Telegram chat ID
   - TRADER_ID: The ID of the trader you want to follow
7. Deploy the service

### Step 5: Set Up UptimeRobot to Keep the Bot Running

1. Sign up for [UptimeRobot.com](https://uptimerobot.com) (free)
2. Add a new monitor
3. Select "HTTP(s)"
4. Name it "Bitget Bot"
5. Enter your Render URL
6. Set check interval to 5 minutes
7. Save the monitor

## Usage

- Visit your bot URL to check if it's running
- Visit your-bot-url/test to test API connections
- Your bot will automatically send notifications to Telegram when your followed trader opens or closes positions

## Troubleshooting

- If Telegram notifications aren't working, verify your bot token and chat ID
- If you're monitoring a group chat, make sure you have the correct chat ID (may start with a minus sign)
- For supergroups, the chat ID typically starts with -100 followed by numbers
- Check the /test endpoint for specific error messages

## Security Notes

- Your API keys are stored as environment variables and not exposed in the code
- The Bitget API permissions are read-only, so the bot cannot make trades
- Always use read-only API permissions when possible
