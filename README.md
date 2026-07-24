<img width="1920" height="1080" alt="Slide 16_9 - 1" src="https://github.com/user-attachments/assets/d1a23678-be24-4524-834b-2367745b664d" />

<div align="center">

# Умная галерея

</div>

---

## О проекте

Сервис асинхронной загрузки и AI-анализа фотографий. Детекция лиц, оценка размытия и качества, поиск дубликатов, группировка идентичных изображений.

Поток: `Upload -> PostgreSQL -> MinIO -> Kafka -> Worker -> gRPC Analyzer -> PostgreSQL`

---

## Быстрый старт

```bash
docker compose up -d
curl http://localhost:8000/healthz
```

Интерактивная API-документация: [https://api.disccsz.ru:51001/redoc](https://api.disccsz.ru:51001/redoc)

<img width="2541" height="1289" alt="image" src="https://github.com/user-attachments/assets/65588aab-8c6b-4488-aa3f-d4ff69aa6142" />


<details>
<summary><b>Kubernetes (kind)</b></summary>

```bash
kind create cluster --name umnaya
docker exec umnaya-control-plane mkdir -p /var/lib/umnaya/{postgres,minio,kafka}
docker build -t umnaya-api .
kind load docker-image umnaya-api --name umnaya
kubectl apply -f k8s/
kubectl port-forward -n umnaya svc/api-service 8000:8000 --address 0.0.0.0
```

</details>

---

## API

| Метод | Путь | Описание |
|--------|------|-------------|
| `POST` | `/api/v1/photo/auth` | Аутентификация VK Mini Apps, получение JWT |
| `POST` | `/api/v1/photos/` | Загрузить фото (JPEG/PNG, до 3MB) |
| `GET` | `/api/v1/photos/` | Список фото (публичные или свои) |
| `GET` | `/api/v1/photos/{id}` | Детали фото с результатами анализа |
| `GET` | `/api/v1/photos/{id}/content` | Presigned URL оригинала и превью |
| `GET` | `/api/v1/duplicate-groups/` | Список групп дубликатов |
| `GET` | `/api/v1/duplicate-groups/{id}` | Детали группы с лучшим фото |
| `GET` | `/healthz` | Health check |
| `GET` | `/readyz` | Readiness check (БД + MinIO) |
| `GET` | `/metrics` | Prometheus метрики |

---

## Технологии

| Категория | Технологии |
|-----------|------------|
| Язык | Python 3.14, asyncio |
| Web Framework | FastAPI, Uvicorn |
| База данных | PostgreSQL 16, SQLAlchemy (async), Alembic, asyncpg |
| Хранилище | MinIO (S3-совместимое) |
| Очередь | Apache Kafka, aiokafka |
| AI / Анализ | gRPC, Protocol Buffers, Pillow |
| Аутентификация | JWT (HS256), HMAC-SHA256, Argon2 |
| Мониторинг | Prometheus, Grafana |
| Развёртывание | Docker Compose, Kubernetes (kind), Nginx |

---

## Структура проекта

```
umnaya_galereya/
+-- app/                      Исходный код (FastAPI + Worker)
|   +-- api/v1/               HTTP роутеры (auth, photos, groups, metrics, health)
|   +-- core/                 Конфиг, ошибки, JWT, логирование, метрики, контекст
|   +-- database/             SQLAlchemy модели: Token, Group, Photos, PhotoAnalysis
|   +-- integrations/         Адаптеры: PostgreSQL, MinIO, Kafka, metrics_db
|   +-- schemas/              Pydantic модели (request/response)
|   +-- services/             Бизнес-логика (VK Auth, Photos, Groups)
|   +-- worker/               Фоновый обработчик (Kafka consumer, gRPC, preview)
|   +-- main.py               Точка входа FastAPI
+-- k8s/                      Kubernetes манифесты (11 файлов)
+-- migrations/               Alembic миграции (3 версии)
+-- docs/                     Документация проекта (MkDocs Material)
+-- docker-compose.yml        Docker оркестрация (8 сервисов)
+-- Dockerfile                Сборка образа
+-- requirements.txt          Python зависимости
+-- prometheus.yml            Конфиг Prometheus
+-- analyzer.proto            gRPC proto контракт
```

Подробно: [https://wwww.disscsz.ru/umnaya_galereya/docs/project-structure/index.html](https://wwww.disscsz.ru/umnaya_galereya/docs/project-structure/index.html)

---

## Переменные окружения

| Компонент | Переменные |
|-----------|------------|
| PostgreSQL | `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` |
| MinIO | `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET_NAME`, `MINIO_PUBLIC_URL` |
| Kafka | `KAFKA_BOOTSTRAP_SERVERS` |
| VK Auth | `VK_SECRET_KEY`, `JWT_EXPIRE_MINUTES` |
| Analyzer | `ANALYSIS_GRPC_URL` |
| Service | `SERVICE_TIMEOUT`, `LOG_LEVEL`, `DB_ECHO` |

Полный справочник: [https://wwww.disscsz.ru/umnaya_galereya/docs/environment/index.html](wwww.disscsz.ru/umnaya_galereya/docs/environment/index.html)

---

## Документация

Полная документация проекта открывается из `https://wwww.disscsz.ru/umnaya_galereya/docs/index.html`:

- Архитектура (C4 Context, Container, Component, ER, Sequence диаграммы)
- API (все эндпоинты с примерами)
- Развёртывание (Docker Compose, Kubernetes)
- Переменные окружения
- Структура проекта
- Метрики Prometheus

---

<div align="center">
  <a href="https://wwww.disscsz.ru/umnaya_galereya/docs/index.html">Документация</a>
  &middot;
  <a href="https://api.disccsz.ru:51001/redoc">ReDoc</a>
  &middot;
  <a href="https://api.disccsz.ru:51001/docs">Swagger UI</a>
</div>
