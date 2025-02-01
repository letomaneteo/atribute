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

# Установка команд в меню
def set_bot_commands():
    url = f"https://api.telegram.org/bot{TOKEN}/setMyCommands"
    commands = {
        "commands": [
            {"command": "start", "description": "Запустить бота"},
            {"command": "menu", "description": "Открыть основное меню"},
            {"command": "gettext", "description": "Отправить текст ИИ"}  # Новая команда
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

# Получение текста с сайта
def fetch_text_from_url():
    try:
        response = requests.get("https://letomaneteo.github.io/myweb/3dls.txt", timeout=5)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при получении текста: {e}")
        return None

# Отправка текста ИИ (DeepSeek)
def send_to_deepseek(input_text):
    url = "https://proxy.tune.app/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "temperature": 0.8,
        "messages": [{"role": "user", "content": input_text}],
        "model": "deepseek/deepseek-r1",
        "stream": False,
        "frequency_penalty": 0,
        "max_tokens": 900
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response_json = response.json()
        
        if "choices" in response_json:
            return response_json["choices"][0]["message"]["content"]
        else:
            return f"Ошибка AI: {response_json.get('error', 'Неизвестная ошибка')}"
    
    except requests.exceptions.Timeout:
        logger.error("Тайм-аут при обращении к DeepSeek API!")
        return "❌ Время ожидания ответа от ИИ истекло."
    
    except Exception as e:
        logger.error(f"Ошибка при вызове API: {e}")
        return "❌ Ошибка при обращении к ИИ."

# Обработка команды /menu
def show_menu(chat_id):
    reply_markup = {
        "keyboard": [
            [{"text": "Смотреть (тех.работы)", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}],
            [{"text": "Смотреть (тех.работы)", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}],
            [{"text": "Смотреть (тех.работы)", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}]
        ],
        "resize_keyboard": True,
        "one_time_keyboard": False
    }
    send_message(chat_id, "Выберите действие:", reply_markup)

# Основной обработчик сообщений
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
                                f"<u>Нажмите, чтобы выбрать действие:</u>"

                reply_markup = {
                    "inline_keyboard": [
                        [{"text": "✨3D товары✨", "web_app": {"url": "https://letomaneteo.github.io/myweb/page1.html"}}],
                        [{"text": "🔗Web-анимация🔗", "url": "https://www.3dls.store/анимация-на-сайте"}],
                        [{"text": "🎮Игра: 22 клика🎮", "web_app": {"url": "https://letomaneteo.github.io/myweb/newpage.html"}}]
                    ]
                }

                send_message(chat_id, response_text, reply_markup)

            elif text == "/menu":
                show_menu(chat_id)

            elif text == "/gettext":
                site_text = fetch_text_from_url()
                if site_text:
                    ai_response = send_to_deepseek(site_text)  # Отправляем текст ИИ
                    send_message(chat_id, ai_response)
                else:
                    send_message(chat_id, "❌ Не удалось получить текст с сайта.")

            else:
                bot_response = send_to_deepseek(text)
                send_message(chat_id, bot_response)

        return "OK", 200
    except Exception as e:
        logger.error(f"Ошибка обработки webhook: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv("PORT", 8080)))
