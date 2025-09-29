FROM python:3.10-slim

# Instalar cron
RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copiar archivo de cron directamente
COPY crontab /etc/cron.d/bot-cron
RUN chmod 0644 /etc/cron.d/bot-cron

# Arrancar cron y el bot
CMD cron && python bot.py
