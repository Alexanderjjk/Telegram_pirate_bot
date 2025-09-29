FROM python:3.10-slim

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY crontab /etc/cron.d/bot-cron
RUN chmod 0644 /etc/cron.d/bot-cron

CMD service cron start && python bot.py