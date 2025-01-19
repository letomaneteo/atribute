from flask import Flask, request
from telegram import Bot
import logging

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"  # Замените на ваш токен
WEBHOOK_URL = "https://web-production-aa772.up.railway.app/webhook"  # Прямая ссылка

# Инициализация бота
bot = Bot(token=TOKEN)

# Синхронная установка вебхука
def set_webhook():
    try:
        webhook_info = bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set successfully: {webhook_info}")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

set_webhook()  # Устанавливаем вебхук при запуске

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Получаем данные от Telegram
        data = request.get_json()
        logger.debug(f"Received data: {data}")  # Логируем входящие данные

        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"]
            if text == "/start":
                chat_id = data["message"]["chat"]["id"]
                logger.info(f"Sending reply to chat_id: {chat_id}")
                bot.send_message(chat_id=chat_id, text="Привет, я бот!")

        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)






