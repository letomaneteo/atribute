import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler
import logging

# Инициализация Flask
app = Flask(__name__)

# Telegram токен
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"

# Инициализация бота
bot = Bot(TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# Установка логирования
logging.basicConfig(level=logging.INFO)

# Обработка команды /start
def start(update, context):
    update.message.reply_text("Привет, я бот!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)

# Вебхук для Telegram
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = Update.de_json(json_str, bot)
    dispatcher.process_update(update)
    return 'OK', 200

# Установка вебхука в Telegram
def set_webhook():
    webhook_url = "https://flask-production-b6fb.up.railway.app/webhook"  # Укажите ваш URL на Railway
    bot.set_webhook(url=webhook_url)

if __name__ == "__main__":
    # Устанавливаем вебхук
    set_webhook()

    # Запуск Flask сервера
    app.run(host='0.0.0.0', port=8080)
