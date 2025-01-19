import os
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, WebhookHandler

# Настройки
DB_PATH = "telegram.db"
TOKEN = os.getenv("BOT_TOKEN")  # Telegram токен через переменные окружения
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Публичный URL для вебхука Telegram
PORT = int(os.getenv("PORT", 8000))  # Порт приложения Flask на Railway

app = Flask(__name__)

# Инициализация базы данных
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 50,
            level INTEGER DEFAULT 0,
            next_points_time TIMESTAMP DEFAULT NULL
        )
        """)
        conn.commit()

# Telegram обработчик команды /start
async def start(update: Update, context):
    user = update.effective_user
    username = user.username or user.first_name

    # Проверяем пользователя в БД
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user.id,))
        user_data = cursor.fetchone()

        if not user_data:
            next_points_time = datetime.now() + timedelta(minutes=5)
            cursor.execute("""
                INSERT INTO users (id, username, points, level, next_points_time)
                VALUES (?, ?, ?, ?, ?)
            """, (user.id, username, 50, 0, next_points_time.isoformat()))
            conn.commit()

    await update.message.reply_text(f"Привет, {username}! Добро пожаловать в бота.")

# Flask маршрут для API
@app.route('/get_user', methods=['GET'])
def get_user():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"error": "user_id отсутствует"}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

    if user:
        return jsonify({
            "id": user[0],
            "username": user[1],
            "points": user[2],
            "level": user[3],
            "next_points_time": user[4]
        })
    return jsonify({"error": "Пользователь не найден"}), 404

# Flask маршрут для Telegram вебхука
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.update_queue.put(update)
    return "OK", 200

# Flask маршрут для проверки статуса
@app.route("/", methods=["GET"])
def index():
    return "Сервер работает!", 200

# Планировщик для обновления очков
def update_points_job():
    current_time = datetime.now()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id FROM users
        WHERE next_points_time IS NOT NULL AND next_points_time <= ?
        """, (current_time,))
        user_ids = cursor.fetchall()

        for user_id, in user_ids:
            cursor.execute("""
            UPDATE users
            SET points = 50, next_points_time = ?
            WHERE id = ?
            """, (current_time + timedelta(minutes=5), user_id))
        conn.commit()

if __name__ == "__main__":
    # Инициализация БД
    init_db()

    # Настройка Telegram-бота
    bot = Bot(token=TOKEN)
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    # Установка вебхука
    bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

    # Запуск планировщика
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_points_job, 'interval', seconds=60)
    scheduler.start()

    # Запуск Flask
    app.run(host="0.0.0.0", port=PORT)
