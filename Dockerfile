FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
        g++ gcc && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove g++ gcc && \
    rm -rf /var/lib/apt/lists/*

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
