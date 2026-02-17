FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY seed_mongodb.py .

CMD ["python", "seed_mongodb.py"]

