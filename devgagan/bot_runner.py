import asyncio
import logging
import os
import sys
import time
from threading import Thread
from flask import Flask

from pyrogram import Client, idle

# ---------- Logging setup ----------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ---------- Keep alive server setup ----------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive and running!"

def run_keep_alive():
    logger.info("Starting keep_alive Flask server on port 8080")
    app.run(host='0.0.0.0', port=8080)

def start_keep_alive():
    t = Thread(target=run_keep_alive)
    t.daemon = True
    t.start()

# ---------- Your Pyrogram bot setup ----------
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# Yeh wahi channel/group jaha log bhejna hai
log_chat_id = os.getenv('LOG_CHAT_ID')  # example: "@yourchannel" or numeric chat_id like -1001234567890

if not all([api_id, api_hash, bot_token, log_chat_id]):
    logger.error("API_ID, API_HASH, BOT_TOKEN, and LOG_CHAT_ID environment variables must be set!")
    sys.exit(1)

app_pyro = Client("my_bot_session", api_id=int(api_id), api_hash=api_hash, bot_token=bot_token)

async def send_telegram_log(message: str):
    try:
        await app_pyro.send_message(log_chat_id, message)
    except Exception as e:
        logger.error(f"Failed to send log message to Telegram: {e}")

async def start_bot():
    logger.info("Starting Pyrogram Client...")
    await app_pyro.start()
    logger.info("Bot started successfully.")
    await send_telegram_log("✅ Bot started successfully.")  # Bot start hone pe bhi log bhejdo
    await idle()
    logger.info("Bot stopped.")
    await send_telegram_log("⚠️ Bot stopped.")

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_bot())
    finally:
        loop.close()

def main():
    start_keep_alive()

    while True:
        try:
            logger.info("Launching bot process...")
            run_bot()
        except Exception as e:
            logger.error(f"Bot crashed with exception: {e}", exc_info=True)
            # Telegram pe bhi crash ka message bhejna hai
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_telegram_log(f"❌ Bot crashed with exception:\n{e}"))
                loop.close()
            except Exception as log_err:
                logger.error(f"Failed to send crash log to Telegram: {log_err}")
            logger.info("Restarting bot after 5 seconds...")
            time.sleep(5)  # 5 second wait before restart
        else:
            logger.info("Bot stopped gracefully.")
            break

if __name__ == "__main__":
    main()
