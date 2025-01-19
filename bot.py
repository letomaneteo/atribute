from flask import Flask, request
from telegram import Bot, Update
import asyncio

app = Flask(__name__)

# Установите ваш токен для бота
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"  # Замените на ваш токен
WEBHOOK_URL = "https://web-production-aa772.up.railway.app/webhook"  # Прямая ссылка

# Инициализация бота
bot = Bot(token=TOKEN)

# Установка вебхука
async def set_webhook():
    await bot.set_webhook(url=WEBHOOK_URL)

@app.before_first_request
def before_first_request():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())

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




