from telegram import Update
from telegram.ext import Application, CommandHandler
from flask import Flask, request
import os

# Токен вашего бота
TOKEN = os.getenv("7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU")

# Создание Flask приложения
app = Flask(__name__)

async def start(update: Update, context):
    """Отправляет сообщение при команде /start"""
    user = update.effective_user
    await update.message.reply_text(f"Привет, {user.first_name}! Я простой бот.")

if __name__ == "__main__":
    # Создание Telegram бота
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Устанавливаем webhook для Telegram бота
    webhook_url = "https://flask-production-b6fb.up.railway.app/webhook"
    application.bot.set_webhook(url=webhook_url)

    # Flask route для получения вебхуков
    @app.route('/webhook', methods=['POST'])
    def webhook():
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.dispatcher.process_update(update)
        return 'OK'

    # Запуск Flask сервера
    app.run(host="0.0.0.0", port=8080)
