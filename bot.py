import os
from flask import Flask, request
import requests
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Переменные окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Telegram Bot Token
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Webhook URL
HF_API_TOKEN = os.getenv("HF_API_TOKEN")  # Hugging Face API Token
HF_MODEL_URL = "https://api-inference.huggingface.co/models/gpt-neo-2.7B"  # URL вашей модели

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

set_webhook()

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.debug(f"Received data: {json.dumps(data, indent=4)}")

        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"]
            chat_id = data["message"]["chat"]["id"]

            # Ответ на команды
            if text == "/start":
                send_message(chat_id, "Привет! Напишите сообщение, и я отвечу с помощью ИИ.")
            else:
                # Обработка текста с помощью Hugging Face
                logger.info(f"Processing text: {text}")
                ai_response = query_hugging_face(text)
                send_message(chat_id, ai_response)

        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500


def query_hugging_face(prompt):
    """
    Отправляет запрос к модели Hugging Face и возвращает результат.
    """
    headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
    payload = {"inputs": prompt}
    
    try:
        response = requests.post(HF_MODEL_URL, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data[0]["generated_text"] if isinstance(data, list) else "Ошибка обработки ответа."
        else:
            logger.error(f"Error from Hugging Face API: {response.status_code} - {response.text}")
            return "Ошибка получения ответа от ИИ."
    except Exception as e:
        logger.error(f"Error querying Hugging Face API: {e}")
        return "Произошла ошибка при обращении к ИИ."

def send_message(chat_id, text, parse_mode='HTML'):
    """
    Отправляет сообщение пользователю в Telegram.
    """
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
