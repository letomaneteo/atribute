from flask import Flask, request
import requests
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"  # Замените на ваш токен
WEBHOOK_URL = "https://web-production-aa772.up.railway.app/webhook"  # Прямая ссылка

# Установка вебхука
def set_webhook():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        params = {'url': WEBHOOK_URL}
        response = requests.post(url, params=params)
        if response.status_code == 200:
            logger.info("Webhook set successfully.")
        else:
            logger.error(f"Error setting webhook: {response.status_code} - {response.text}")
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
                user_name = data["message"]["from"]["first_name"]
                user_id = data["message"]["from"]["id"]
                logger.info(f"Sending reply to chat_id: {chat_id}")

                # Создаем кнопку с ссылкой на ваше приложение в маленьком окне
                keyboard = [
                    [InlineKeyboardButton("Перейти в приложение", web_app={"url": f"https://letomaneteo.github.io/myweb/newpage.html?user_id={user_id}"})]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Отправляем ответ на команду /start с кнопкой
                send_message(chat_id, f"Привет, {user_name}! Твой ID: {user_id}. Перейди по кнопке ниже, чтобы открыть приложение.", reply_markup=reply_markup)

        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500

def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'Markdown', 'reply_markup': reply_markup}
        response = requests.post(url, json=params)
        if response.status_code == 200:
            logger.info(f"Message sent to {chat_id}")
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

