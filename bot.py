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
TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Хранение состояния пользователей (ждет ли бот сообщение для ИИ)
user_state = {}

def set_bot_commands():
    url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
    commands = {"commands": [
        {"command": "start", "description": "Запустить бота"},
        {"command": "menu", "description": "Открыть основное меню"}
    ]}
    requests.post(url, json=commands)

def set_webhook():
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
    requests.post(url, params={'url': WEBHOOK_URL})

set_bot_commands()
set_webhook()

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    if reply_markup:
        params['reply_markup'] = json.dumps(reply_markup)
    requests.post(url, params=params)

def show_menu(chat_id):
    reply_markup = {
        "keyboard": [
            [{"text": "🤖 Вызвать ИИ"}],
            [{"text": "✨ Шоурумы интерактивных 3D товаров", "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}}],
            [{"text": "🎮 Игра: Победа в 22 клика", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}]
        ],
        "resize_keyboard": True
    }
    send_message(chat_id, "Выберите действие:", reply_markup)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"]
        chat_id = data["message"]["chat"]["id"]
        user_id = data["message"]["from"]["id"]
        
        if text == "/start":
            send_message(chat_id, "Привет! Используйте /menu для навигации.")
        elif text == "/menu":
            show_menu(chat_id)
        elif text == "🤖 Вызвать ИИ":
            user_state[user_id] = "awaiting_ai"
            send_message(chat_id, "ИИ активирован! Напишите ваш вопрос.")
        elif user_id in user_state and user_state[user_id] == "awaiting_ai":
            response_text = chat_with_ai(text)
            send_message(chat_id, response_text)
            del user_state[user_id]  # Сброс состояния после ответа
        else:
            send_message(chat_id, "Неизвестная команда. Используйте /menu.")
    return "OK", 200

def chat_with_ai(user_message):
    url = "https://proxy.tune.app/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    data = {
        "temperature": 0.9,
        "messages": [
            {"role": "system", "content": "Вы - умный помощник"},
            {"role": "user", "content": user_message}
        ],
        "model": "deepseek/deepseek-v3"
    }
    response = requests.post(url, headers=headers, json=data)
    try:
        response_json = response.json()
        return response_json.get("choices", [{}])[0].get("message", {}).get("content", "Ошибка ответа ИИ")
    except:
        return "Ошибка обработки ответа от ИИ."

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 8080)))
