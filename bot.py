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

def set_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    params = {'url': WEBHOOK_URL}
    response = requests.post(url, params=params)
    if response.status_code == 200:
        logger.info("Webhook установлен!")
    else:
        logger.error(f"Ошибка установки вебхука: {response.text}")

set_webhook()

# 🔹 Функция загрузки текста с GitHub

def fetch_github_text():
    try:
        response = requests.get(BASE_URL)
        response.raise_for_status()
        return response.text.strip() if response.text.strip() else "Нет данных."
    except Exception as e:
        logger.error(f"Ошибка загрузки текста с GitHub: {e}")
        return "Ошибка загрузки данных."

github_text = fetch_github_text()
logger.info(f"Загруженный текст: {github_text[:200]}...")

# 🔹 DeepSeek API

def chat_with_deepseek(user_message):
    url = "https://proxy.tune.app/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "temperature": 0.8,
        "messages": [
            {"role": "system", "content": f"Используй этот текст для ответов: {github_text}"},
            {"role": "user", "content": user_message}
        ],
        "model": "deepseek/deepseek-r1",
        "stream": False,
        "frequency_penalty": 0,
        "max_tokens": 900
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        return response_json["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Ошибка AI: {e}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.debug(f"Получены данные: {data}")

        if "message" in data and "text" in data["message"]:
            text = data["message"]["text"]
            chat_id = data["message"]["chat"]["id"]

            if text == "/start":
                user_name = data["message"]["from"].get("username", "неизвестно")
                response_text = f"<b>Здравствуйте, {user_name}!</b>\n" \
                                f"Вы нажали: {text}, выбирайте, что хотите посмотреть"
                
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": "✨Шоурумы интерактивных 3D товаров✨", "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}}],
                        [{"text": "🔗Все о web-анимации🔗", "url": "https://www.3dls.store/анимация-на-сайте"}],
                        [{"text": "🎮Игра: Победа в 22 клика🎮", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}]
                    ]
                }
                send_message(chat_id, response_text, reply_markup)
            else:
                ai_response = chat_with_deepseek(text)
                send_message(chat_id, ai_response)
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
    return "OK", 200

def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        response = requests.post(url, params=params)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
