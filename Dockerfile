FROM python:3.10-slim

# Отключаем кэширование и устанавливаем переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота
COPY . .

# Открываем порт (Railway подставит свой)
EXPOSE ${PORT:-8000}

# Запускаем бота через Gunicorn
CMD exec gunicorn --bind :${PORT:-8000} --workers 1 bot:app
