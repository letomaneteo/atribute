from flask import Flask, request
import requests
import logging
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Токены
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Telegram API Token
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL для вебхука
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # OpenRouter API Token

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

# Функция запроса к OpenRouter
def chat_with_ai(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "liquid/lfm-7b",  # Менее затратная модель
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 100  # Ограничение длины ответа
    }

    response = requests.post(url, headers=headers, json=data)
    response_json = response.json()

    if "choices" in response_json:
        return response_json["choices"][0]["message"]["content"]
    else:
        return f"Ошибка OpenRouter: {response_json.get('error', 'Неизвестная ошибка')}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")

        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"]
            chat_id = data["message"]["chat"]["id"]

            if text == "/start":
                user_name = data["message"]["from"].get("username", "неизвестно")
                user_id = data["message"]["from"]["id"]
                response_text = f"<b>Здравствуйте, {user_name}!</b>\n" \
                                f"<i>Ваш телеграм ID: {user_id}.</i>\n" \
                                f"<u>Вы нажали: {text}</u>"

                # Создаем inline кнопки
                reply_markup = {
                    "inline_keyboard": [
                        [
                            {"text": "✨Смотреть интерактивные 3D модели✨", "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}}
                        ],
                        [
                            {"text": "🔗Все о web-анимации🔗", "url": "https://www.3dls.store/%D0%B0%D0%BD%D0%B8%D0%BC%D0%B0%D1%86%D0%B8%D1%8F-%D0%BD%D0%B0-%D1%81%D0%B0%D0%B9%D1%82%D0%B5"}
                        ],
                        [
                            {"text": "🎮Поиграть (Победить за 22 клика)🎮", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}
                        ]
                    ]
                }

                # Преобразуем reply_markup в строку JSON с обработкой ошибок
                try:
                    reply_markup_json = json.dumps(reply_markup)
                except Exception as e:
                    logger.error(f"Error converting reply_markup to JSON: {e}")
                    reply_markup_json = None

                # Отправляем ответ на команду /start с inline кнопками
                send_message(chat_id, response_text, reply_markup_json)

            else:
                bot_response = chat_with_ai(text)  # Отправляем текст в OpenRouter
                send_message(chat_id, bot_response)

        return "OK", 200  # Один return в конце
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500


# Функция отправки сообщений в Telegram
def send_message(chat_id, text, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        response = requests.post(url, params=params)
        if response.status_code == 200:
            logger.info(f"Message sent to {chat_id}")
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

