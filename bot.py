from flask import Flask, request
import requests
import logging
import json
import os
from bs4 import BeautifulSoup

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Токены
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Telegram API Token
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL для вебхука
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")  # OpenRouter API Token

BASE_URL = "https://raw.githubusercontent.com/letomaneteo/myweb/main/3dls.txt"

# Установка команд в меню
def set_bot_commands():
    url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
    commands = {
        "commands": [
            {"command": "start", "description": "Запустить бота"},
            {"command": "menu", "description": "Открыть основное меню"}
        ]
    }
    response = requests.post(url, json=commands)
    if response.status_code == 200:
        logger.info("Команды успешно добавлены!")
    else:
        logger.error(f"Ошибка при добавлении команд: {response.text}")

set_bot_commands()

# Установка вебхука
def set_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    params = {'url': WEBHOOK_URL}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        logger.info("Webhook установлен!")
    else:
        logger.error(f"Ошибка установки вебхука: {response.text}")

set_webhook()

# Функция получения текста с GitHub
def get_text_from_github():
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            return response.text[:8000]  # Ограничение текста
        else:
            return "Ошибка загрузки данных с GitHub."
    except Exception as e:
        return f"Ошибка при парсинге: {e}"

site_text = get_text_from_github()
logger.info(f"Длина загруженного текста: {len(site_text)} символов")

# AI DeepSeek
def chat_with_deepseek(user_message):
    url = "https://proxy.tune.app/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "temperature": 0.8,
        "messages": [
            {"role": "system", "content": f"Используй этот текст для ответов: {site_text}"},
            {"role": "user", "content": user_message}
        ],
        "model": "deepseek/deepseek-r1",
        "stream": False,
        "max_tokens": 900
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        return response.json().get("choices", [{}])[0].get("message", {}).get("content", "Ошибка AI")
    except Exception as e:
        return f"Ошибка AI: {e}"

# Обработчик сообщений
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.debug(f"Получены данные: {data}")
        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"]
            chat_id = data["message"]["chat"]["id"]
            if text == "/start":
                send_message(chat_id, "Привет! Я бот.")
            else:
                response_text = chat_with_deepseek(text)
                send_message(chat_id, response_text)
    except Exception as e:
        logger.error(f"Ошибка в webhook: {e}")
    return "OK", 200

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {'chat_id': chat_id, 'text': text}
    requests.post(url, params=params)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
