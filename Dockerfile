# Используем официальный образ Python 3.9 Alpine
FROM python:3.9-alpine

# Устанавливаем системные зависимости для сборки и psutil
# Удаляем кэш пакетов для уменьшения размера
RUN apk add --no-cache gcc musl-dev linux-headers

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта в контейнер
COPY . .

# Удаляем системные зависимости, так как они больше не нужны после установки Python-пакетов
RUN apk del gcc musl-dev linux-headers

# Указываем команду для запуска приложения
# Запускаем сервер на 0.0.0.0, чтобы он был доступен снаружи контейнера
CMD ["python", "app/run.py", "--host", "0.0.0.0", "--port", "8000"]