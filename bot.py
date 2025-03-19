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

# Функция отправки сообщений
def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
        if reply_markup:
            params['reply_markup'] = json.dumps(reply_markup)
        response = requests.post(url, params=params)
        if response.status_code == 200:
            logger.info(f"Сообщение отправлено в {chat_id}")
        else:
            logger.error(f"Ошибка отправки: {response.text}")
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")

# Функция обработки команды /menu
def show_menu(chat_id):
    reply_markup = {
        "keyboard": [
            [{"text": "Смотреть (тех.работы)", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}],
            [{"text": "Смотреть (тех.работы)", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }

    send_message(chat_id, "Выберите действие:", reply_markup)

# Обработка сообщений
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
                user_id = data["message"]["from"]["id"]
                response_text = f"<b>Здравствуйте, {user_name}!</b>\n" \
                                f"<i>Ваш телеграм ID: {user_id}, но это будет наш секрет.</i>\n" \
                                f"<u>Вы нажали: {text}, а потому выбирайте</u>"
                
                reply_markup = {
                    "inline_keyboard": [
                        [{"text": "✨3D меню✨", "web_app": {"url": "https://letomaneteo.github.io/myweb/menu.html"}}],
                        [{"text": "✨Шоурумы интерактивных 3D товаров✨", "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}}],
                        [{"text": "🔗Все о web-анимации (сайт)🔗", "url": "https://www.3dls.store/анимация-на-сайте"}],
                        [{"text": "🎮Игра: Победа в 22 клика🎮", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}],
                       [{"text": "🤖Тест: Идеальный АИ. Выиграй приз.🤖", "url": "https://t.me/AIIdealBot"}]

                    ]
                }
                
                send_message(chat_id, response_text, reply_markup)
               # send_message(chat_id, f"ℹ️ {user_name}, привет, я DeepSeek, я готов тебе ответить!")

            elif text == "/menu":
                show_menu(chat_id)  # Показываем кнопки меню

            else:
                pass  # Ничего не делать

               # bot_response = chat_with_ai(text)
               # send_message(chat_id, bot_response)

        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return f"Error: {e}", 500

def chat_with_ai(user_message):
    url = "https://proxy.tune.app/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",  # API-ключ из переменной окружения
        "Content-Type": "application/json"
    }
    data = {
        "temperature": 0.9,
        "messages": [
            {"role": "system", "content": "You are TuneStudio"},
            {"role": "user", "content": user_message}
        ],
        "model": "deepseek/deepseek-v3",
        "stream": False,
        "frequency_penalty": 0.2,
        "max_tokens": 100
    }

    response = requests.post(url, headers=headers, json=data)
    
    try:
        response_json = response.json()
        if "choices" in response_json:
            return response_json["choices"][0]["message"]["content"]
        else:
            return f"Ошибка Tune API: {response_json.get('error', 'Неизвестная ошибка')}"
    except Exception as e:
        return f"Ошибка обработки ответа API: {e}"
       
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 8080)))
