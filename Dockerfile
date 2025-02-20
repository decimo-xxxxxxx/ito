FROM python:3.11

WORKDIR /app

RUN pip install --no-cache-dir discord.py

COPY . .

CMD ["python", "ito-dealer.py"]
