from flask import Flask, request
import requests
import logging
import json  # Добавляем модуль для преобразования в JSON
import os  # Для работы с переменными окружения

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Получаем токен из переменной окружения
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Получаем URL вебхука из переменной окружения

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
                user_name = data["message"]["from"].get("username", "неизвестно")
                user_id = data["message"]["from"]["id"]
                logger.info(f"Sending reply to chat_id: {chat_id} (User: {user_name}, ID: {user_id})")
                
                # Формируем текст для ответа
                response_text = f"<b>Здравствуйте, {user_name}!</b>\n" \
                                f"<i>Ваш телеграм ID: {user_id}.</i>\n" \
                                f"<u>Вы нажали: {text}</u>"

                # Создаем inline кнопки
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {
                                "text": "✨Смотреть интерактивные 3D модели✨",
                                "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}  # Ссылка на приложение
                            }
                        ],
                        [
                            {
                                "text": "🔗Все о web-анимации🔗",
                                "url": "https://example.com"  # Ссылка на внешний ресурс
                            }
                        ],
                        [
                            {
                                "text": "🎮Поиграть(Победить за 22 клика)🎮",
                                "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}  # Callback для обработки
                            }
                        ]
                    ]
                }

                # Преобразуем reply_markup в строку JSON с обработкой ошибок
                try:
                    reply_markup_json = json.dumps(reply_markup)
                except Exception as e:
                    logger.error(f"Error converting reply_markup to JSON: {e}")
                    reply_markup_json = None  # Установите значение по умолчанию

                # Отправляем ответ на команду /start с inline кнопками
                send_message(chat_id, response_text, reply_markup_json)

        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500

def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup:
            params['reply_markup'] = reply_markup  # Отправляем reply_markup как строку JSON
        response = requests.post(url, params=params)
        if response.status_code == 200:
            logger.info(f"Message sent to {chat_id}")
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
