from flask import Flask, request
import requests
import logging
import json  # Добавляем модуль для преобразования в JSON
import os  # Для работы с переменными окружения

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Установите ваш токен для бота и Hugging Face
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Получаем токен из переменной окружения
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Получаем URL вебхука из переменной окружения
HF_TOKEN = os.getenv("HF_TOKEN")  # Токен Hugging Face для работы с ИИ

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
            chat_id = data["message"]["chat"]["id"]

            if text == "/start":
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
                                "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}
                            }
                        ],
                        [
                            {
                                "text": "🔗Все о web-анимации🔗",
                                "url": "https://www.3dls.store/%D0%B0%D0%BD%D0%B8%D0%BC%D0%B0%D1%86%D0%B8%D1%8F-%D0%BD%D0%B0-%D1%81%D0%B0%D0%B9%D1%82%D0%B5"
                            }
                        ],
                        [
                            {
                                "text": "🎮Поиграть(Победить за 22 клика)🎮",
                                "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}
                            }
                        ]
                    ]
                }

                # Преобразуем reply_markup в строку JSON
                reply_markup_json = json.dumps(reply_markup)

                # Отправляем ответ на команду /start с inline кнопками
                send_message(chat_id, response_text, reply_markup_json)

            else:
                # Обработка сообщения через Hugging Face
                response_text = get_ai_response(text)
                send_message(chat_id, response_text)

        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500

def get_ai_response(user_input):
    try:
        # Настраиваем запрос к HuggingFace
        huggingface_url = "https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill"
        headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_TOKEN')}"  # Токен из переменной окружения
        }
        payload = {"inputs": user_input}

        # Отправляем запрос к API
        response = requests.post(huggingface_url, headers=headers, json=payload)

        # Проверяем статус ответа
        if response.status_code != 200:
            logger.error(f"Error from HuggingFace API: {response.status_code} - {response.text}")
            return "Извините, возникла ошибка при обработке вашего запроса."

        # Обрабатываем ответ
        response_data = response.json()

        # Проверяем тип данных в ответе
        if isinstance(response_data, dict):
            # Если ответ — словарь
            return response_data.get("generated_text", "Извините, я не смог найти подходящий ответ.")
        elif isinstance(response_data, list) and len(response_data) > 0:
            # Если ответ — список
            return response_data[0].get("generated_text", "Извините, я не смог найти подходящий ответ.")
        else:
            # Непредвиденный формат данных
            logger.error(f"Unexpected response format: {response_data}")
            return "Произошла ошибка при обработке ответа от ИИ."

    except Exception as e:
        # Логируем ошибку
        logger.error(f"Error during AI request: {e}")
        return "Произошла ошибка при общении с ИИ."


def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup:
            params['reply_markup'] = reply_markup
        response = requests.post(url, params=params)
        if response.status_code == 200:
            logger.info(f"Message sent to {chat_id}")
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
