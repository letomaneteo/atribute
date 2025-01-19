from flask import Flask, request
from telegram import Bot, Update

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"  # Замените на ваш токен
WEBHOOK_URL = "https://flask-production-b6fb.up.railway.app/webhook"  # Прямая ссылка

# Инициализация бота
bot = Bot(token=TOKEN)

# Установка вебхука
bot.set_webhook(url=WEBHOOK_URL)

# Обработка вебхука
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Получаем обновление от Telegram
        update = Update.de_json(request.get_json(), bot)

        # Ответ на сообщение
        bot.send_message(chat_id=update.message.chat_id, text="Привет, бот работает!")

        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)


