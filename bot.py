from flask import Flask, request
from telegram import Bot, Update
import logging

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"  # Замените на ваш токен
WEBHOOK_URL = "https://web-production-aa772.up.railway.app.app/webhook"  # Прямая ссылка

# Инициализация бота
bot = Bot(token=TOKEN)

# Установка вебхука
bot.set_webhook(url=WEBHOOK_URL)

# Обработка вебхука
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = Update.de_json(request.get_json(), bot)
        bot.send_message(chat_id=update.message.chat_id, text="Привет, бот работает!")
        return "OK", 200
    except Exception as e:
        logging.error(f"Error in webhook: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)



