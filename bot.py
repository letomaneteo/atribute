from flask import Flask, request
from telegram import Bot

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"  # Замените на ваш токен
WEBHOOK_URL = "https://flask-production-b6fb.up.railway.app/webhook"  # Прямая ссылка

# Инициализация бота
bot = Bot(token=TOKEN)

# Установка вебхука
bot.set_webhook(url=WEBHOOK_URL)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()

    # Проверяем, что в сообщении команда /start
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"]
        if text == "/start":
            chat_id = data["message"]["chat"]["id"]
            bot.send_message(chat_id=chat_id, text="Привет, я бот!")

    return "OK", 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)




