# Используем официальный образ Python
FROM python:3.10-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все исходные файлы
COPY . .

# Открываем порт 8000
EXPOSE 80

# Запускаем FastAPI сервер
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]