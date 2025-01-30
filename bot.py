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

# Устанавливаем команды при старте
set_bot_commands()

def menu(update, context):
    chat_id = update["message"]["chat"]["id"]
    
    reply_markup = {
        "keyboard": [
            [{"text": "✨ Тематические шоурумы"}],
            [{"text": "🔗 Всё о web-анимации"}],
            [{"text": "🎮 Игра: Победа в 22 клика"}]
        ],
        "resize_keyboard": True,  # Автоматическая подгонка клавиатуры
        "one_time_keyboard": False  # Клавиатура остаётся на экране
    }

    send_message(chat_id, "Выберите действие:", reply_markup)

# Добавляем обработчик в вебхук
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
                                f"<i>Ваш телеграм ID: {user_id}, но это наш секрет.</i>\n" \
                                f"<u>Вы нажали: {text}, а потому выбирайте, что хотите посмотреть</u>"

                send_message(chat_id, response_text)

            elif text == "/menu":
                menu(update, context)  # Показываем меню

            else:
                bot_response = chat_with_ai(text)
                send_message(chat_id, bot_response)

        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500

# Функция запроса к OpenRouter
def chat_with_ai(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "liquid/lfm-7b",
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 100
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
                                f"<i>Ваш телеграм ID: {user_id}, но это наш секрет.</i>\n" \
                                f"<u>Вы нажали: {text}, а потому выбирайте, что хотите посмотреть</u>"
                
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": "✨Тематические шоурумы интерактивных 3D товаров✨", "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}}],
                        [{"text": "🔗Все о web-анимации🔗", "url": "https://www.3dls.store/%D0%B0%D0%BD%D0%B8%D0%BC%D0%B0%D1%86%D0%B8%D1%8F-%D0%BD%D0%B0-%D1%81%D0%B0%D0%B9%D1%82%D0%B5"}],
                        [{"text": "🎮Игра: Победа в 22 клика🎮", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}]
                    ]
                }
                
                send_message(chat_id, response_text, reply_markup)
                send_message(chat_id, f"ℹ️ {user_name}, напишите в чат и пообщайтесь с ИИ!")

            else:
                bot_response = chat_with_ai(text)
                send_message(chat_id, bot_response)
        
        return "OK", 200
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return f"Error: {e}", 500

# Функция отправки сообщений в Telegram
def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        response = requests.post(url, params=params)
        if response.status_code == 200:
            logger.info(f"Message sent to {chat_id}")
        else:
            logger.error(f"Error sending message: {response.status_code} - {response.text}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
