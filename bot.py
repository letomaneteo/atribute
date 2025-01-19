import asyncio
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler
from apscheduler.schedulers.background import BackgroundScheduler
import logging
import json

# Настройки
DB_PATH = "telegram.db"
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Явно разрешаем все домены

# Telegram токен
TOKEN = "7815366595:AAGA-HPHVPqyTQn579uoeM7yPDRrf-UIdsU"

# Инициализация логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Инициализация базы данных
def init_db():
    """Создает таблицу, если её ещё нет"""
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

# Проверяем, есть ли пользователь в базе данных, иначе создаем
def get_or_create_user(user_id, username):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            next_points_time = datetime.now() + timedelta(minutes=5)
            cursor.execute("""
            INSERT INTO users (id, username, points, level, next_points_time)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, username, 50, 0, next_points_time.isoformat()))
            conn.commit()
            return {
                "id": user_id, "username": username, "points": 50,
                "level": 0, "next_points_time": next_points_time.isoformat()
            }
        else:
            return {
                "id": user[0], "username": user[1], "points": user[2],
                "level": user[3], "next_points_time": user[4]
            }

# Telegram обработчик команды /start
async def start(update: Update, context):
    user = update.effective_user
    chat_id = user.id
    username = user.username or user.first_name

    user_data = get_or_create_user(user.id, username)

    message = f"Привет, {username}! Добро пожаловать в приложение.\n"
    message += f"Твои очки: {user_data['points']}, уровень: {user_data['level']}."

    keyboard = [
        [InlineKeyboardButton("Перейти в приложение", web_app={"url": f"https://letomaneteo.github.io/myweb/555.html?user_id={user.id}"})]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)

# Функция обновления очков
def update_user_points(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        current_time = datetime.now()

        cursor.execute("""
        SELECT points, next_points_time, username
        FROM users
        WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()

        if user:
            points, next_points_time, username = user

            if next_points_time:
                next_points_time = datetime.fromisoformat(next_points_time)

            if points == 0 and (not next_points_time or current_time >= next_points_time):
                points = 50
                next_points_time = current_time + timedelta(minutes=5)
                cursor.execute("""
                UPDATE users
                SET points = ?, next_points_time = ?
                WHERE id = ?
                """, (points, next_points_time.isoformat(), user_id))
                conn.commit()

                try:
                    application.bot.send_message(chat_id=user_id, text=f"Ваши очки были обновлены до 50, {username}!")
                except Exception as e:
                    logging.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

# Задача для обновления очков
def update_points_job():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        current_time = datetime.now()

        cursor.execute("""
        SELECT id
        FROM users
        WHERE next_points_time IS NOT NULL AND next_points_time <= ?
        """, (current_time,))
        user_ids = cursor.fetchall()

        for user_id, in user_ids:
            update_user_points(user_id)

# Flask маршруты
@app.route('/edit_points', methods=['POST'])
def edit_points():
    try:
        data = request.get_json()
        if not data or 'user_id' not in data or 'points' not in data:
            return jsonify({"status": "error", "message": "Данные некорректны или отсутствуют"}), 400

        user_id = int(data['user_id'])
        points = int(data['points'])

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET points = ? WHERE id = ?", (points, user_id))
            conn.commit()

        return jsonify({"status": "success", "message": "Points updated successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_user', methods=['GET'])
def get_user():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"error": "user_id отсутствует"}), 400

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT id, username, points, level, next_points_time
        FROM users
        WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()

        if user:
            user_id, username, points, level, next_points_time = user
            return jsonify({
                "id": user_id,
                "username": username,
                "points": points,
                "level": level,
                "next_points_time": next_points_time
            }), 200

        return jsonify({"error": "Пользователь не найден"}), 404

# Обработчик для вебхука
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data(as_text=True)
        logging.info(f"Received webhook payload: {json_str}")
        update = Update.de_json(json.loads(json_str), application.bot)
        application.process_update(update)
        return '', 200
    except Exception as e:
        logging.error(f"Ошибка при обработке вебхука: {e}")
        return '', 500

if __name__ == "__main__":
    init_db()

    # Запуск планировщика задач
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_points_job, 'interval', seconds=60)
    scheduler.start()

    # Запуск Telegram-бота
    application = Application.builder().token(TOKEN).build()

    # Установка вебхука
    application.bot.set_webhook(url="https://flask-production-b6fb.up.railway.app/webhook")

    application.add_handler(CommandHandler("start", start))

    # Запуск Flask-сервера
    app.run(host="0.0.0.0", port=8080)
