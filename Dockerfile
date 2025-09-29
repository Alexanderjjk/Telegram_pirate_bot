# Imagen base con Python 3.10
FROM python:3.10-slim

# Instalar cron y limpiar caché
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Copiar archivo de tareas programadas
COPY crontab /etc/cron.d/bot-cron

# Dar permisos correctos al archivo de cron
RUN chmod 0644 /etc/cron.d/bot-cron

# Arrancar cron y el bot
CMD service cron start && python bot.py