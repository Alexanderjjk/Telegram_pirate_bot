FROM python:3.10-slim

# Instalar cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del bot
COPY . .

# Copiar archivo de cron
COPY crontab /etc/cron.d/bot-cron

# Dar permisos y habilitar cron
RUN chmod 0644 /etc/cron.d/bot-cron

# Arrancar cron y el bot
CMD service cron start && python bot.py