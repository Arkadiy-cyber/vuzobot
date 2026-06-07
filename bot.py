import subprocess
import sys

# Функция для установки пакетов
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Список необходимых пакетов
required_packages = ['Flask', 'gunicorn', 'aiogram']

for package in required_packages:
    try:
        import(package.lower() if package != 'Flask' else 'flask')
    except ImportError:
        print(f"Устанавливаю {package}...")
        install(package)

# Теперь импорты должны работать
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
# ... остальные импорты

app = Flask(name)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/set_webhook')
def set_webhook():
    return "OK", 200

# Твоя полная логика бота (добавь позже)

