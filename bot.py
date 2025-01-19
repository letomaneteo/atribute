import os
from flask import Flask, request
from telegram import Bot, Update
import logging

app = Flask(__name__)

# Telegram token
TOKEN = '7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU'
bot = Bot(token=TOKEN)

# Установка вебхука
webhook_url = 'https://flask-production-b6fb.up.railway.app/webhook'  # Используйте ваш реальный URL с Railway
bot.set_webhook(url=webhook_url)

# Вебхук для обработки запросов от Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Получаем обновление от Telegram
        update = Update.de_json(request.get_json(), bot)

        # Ответ на сообщение
        bot.send_message(chat_id=update.message.chat_id, text="Привет, бот работает!")

        return "OK", 200
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return "Error", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)

