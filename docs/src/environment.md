# Переменные окружения

Конфигурация загружается из `.env` через `pydantic-settings` (`app/core/config.py:3`).

---

## PostgreSQL

| Переменная       | Тип    | По умолчанию     | Обязательная | Описание                           |
|------------------|--------|------------------|:------------:|------------------------------------|
| `DB_USER`        | string | —                | да           | Пользователь БД                    |
| `DB_PASSWORD`    | string | —                | да           | Пароль БД                          |
| `DB_HOST`        | string | —                | да           | Хост БД (например `postgres`)      |
| `DB_PORT`        | int    | —                | да           | Порт БД (внутренний 5432)          |
| `DB_NAME`        | string | —                | да           | Название БД (`photo_analysis`)     |

URL подключения формируется автоматически:
```
postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}
```

---

## MinIO

| Переменная            | Тип    | По умолчанию        | Обязательная | Описание                                   |
|-----------------------|--------|---------------------|:------------:|--------------------------------------------|
| `MINIO_ENDPOINT`      | string | —                   | да           | Адрес MinIO (например `localhost:9100`)    |
| `MINIO_ROOT_USER`     | string | —                   | да           | Пользователь MinIO                         |
| `MINIO_ROOT_PASSWORD` | string | —                   | да           | Пароль MinIO                               |
| `MINIO_BUCKET_NAME`   | string | —                   | да           | Название bucket (`photo-bucket`)           |
| `MINIO_PUBLIC_URL`    | string | `""`                | нет          | Публичный URL для подмены в presigned-url  |

---

## Kafka

| Переменная                  | Тип    | По умолчанию | Обязательная | Описание                        |
|-----------------------------|--------|--------------|:------------:|---------------------------------|
| `KAFKA_BOOTSTRAP_SERVERS`   | string | —            | да           | Адрес Kafka (например `kafka:9092`) |

---

## gRPC Analyzer

| Переменная          | Тип    | По умолчанию                   | Обязательная | Описание                        |
|---------------------|--------|--------------------------------|:------------:|---------------------------------|
| `ANALYSIS_GRPC_URL` | string | `45.132.19.101:50051`          | нет          | Адрес внешнего gRPC анализатора |

---

## VK Authentication

| Переменная          | Тип    | По умолчанию     | Обязательная | Описание                        |
|---------------------|--------|------------------|:------------:|---------------------------------|
| `VK_SECRET_KEY`     | string | —                | да           | Секретный ключ VK приложения    |
| `JWT_EXPIRE_MINUTES`| int    | `525600` (1 год)  | нет          | Время жизни JWT в минутах       |

---

## Service

| Переменная       | Тип    | По умолчанию | Обязательная | Описание                      |
|------------------|--------|--------------|:------------:|-------------------------------|
| `SERVICE_TIMEOUT`| int    | —            | да           | Таймаут для внешних вызовов (сек) |

---

## Logging

| Переменная  | Тип    | По умолчанию | Обязательная | Описание                                  |
|-------------|--------|--------------|:------------:|-------------------------------------------|
| `LOG_LEVEL` | string | `INFO`       | нет          | Уровень логирования: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DB_ECHO`   | bool   | `false`      | нет          | Вывод SQL запросов в лог (для отладки)    |

---

## Пример `.env`

```ini
# === PostgreSQL ===
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5435
DB_NAME=photo_analysis

# === MinIO ===
MINIO_ENDPOINT=localhost:9100
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET_NAME=photo-bucket

# === Kafka ===
KAFKA_BOOTSTRAP_SERVERS=kafka:9092

# === Logging ===
LOG_LEVEL=INFO
DB_ECHO=false

# === Service ===
SERVICE_TIMEOUT=10

# === VK Auth ===
VK_SECRET_KEY=your_vk_secret_key_here
JWT_EXPIRE_MINUTES=525600

# === gRPC Analyzer ===
ANALYSIS_GRPC_URL=45.132.19.101:50051
```
