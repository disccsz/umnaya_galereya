# Структура проекта

```
umnaya_galereya/
│
├── app/                              # Основной код приложения
│   ├── api/                          # HTTP слой (FastAPI)
│   │   ├── v1/                       # Версия API v1
│   │   │   ├── auth.py               #   POST /api/v1/photo/auth
│   │   │   ├── photos.py             #   CRUD для фото
│   │   │   ├── groups.py             #   Группы дубликатов
│   │   │   ├── metrics.py            #   GET /metrics (Prometheus)
│   │   │   ├── healthz.py            #   GET /healthz
│   │   │   └── readyz.py             #   GET /readyz
│   │   └── depends.py                #   FastAPI dependencies (get_current_user)
│   │
│   ├── core/                         # Ядро: настройки, ошибки, метрики
│   │   ├── config.py                 #   Pydantic Settings (.env)
│   │   ├── errors.py                 #   AppException, ErrorCodes, ErrorResponse
│   │   ├── jwt_utils.py              #   JWT encode/decode (HMAC-SHA256)
│   │   ├── log.py                    #   Настройка логирования
│   │   ├── metrics.py                #   Prometheus counter/histogram
│   │   └── context.py                #   ContextVar для request_id
│   │
│   ├── database/                     # Слой доступа к БД
│   │   ├── models.py                 #   SQLAlchemy модели: Token, Group, Photos, PhotoAnalysis
│   │   └── database.py               #   async engine + session factory
│   │
│   ├── integrations/                 # Интеграции с внешними системами
│   │   ├── postgreesql.py            #   PhotoDatabase, GroupDatabase, TokenDatabase
│   │   ├── minio.py                  #   MinIOStorage (S3)
│   │   ├── kafka.py                  #   KafkaProducer
│   │   └── metrics_db.py             #   Prometheus метрики из БД
│   │
│   ├── schemas/                      # Pydantic модели (request/response)
│   │   ├── auth.py                   #   VKAuthRequest, VKAuthResponse
│   │   ├── photos.py                 #   Upload/Get/List photo схемы
│   │   └── groups.py                 #   DuplicateGroup схемы
│   │
│   ├── services/                     # Бизнес-логика
│   │   ├── auth_service.py           #   VKAuthService (верификация подписи)
│   │   ├── photos_service.py         #   PhotoService (загрузка, список, детали)
│   │   └── groups_service.py         #   GroupService (список, детали групп)
│   │
│   ├── worker/                       # Фоновый обработчик
│   │   ├── __main__.py               #   Точка входа: python -m app.worker
│   │   ├── consumer.py               #   Kafka consumer
│   │   ├── processor.py              #   Логика обработки фото
│   │   ├── database.py               #   Операции с БД для worker
│   │   ├── minio_client.py           #   MinIO клиент для worker
│   │   ├── grpc_client.py            #   gRPC клиент анализатора
│   │   ├── hasher.py                 #   SHA256 + перцептивный хеш
│   │   └── preview.py                #   Генерация preview (Pillow)
│   │
│   └── main.py                       # FastAPI приложение (lifespan, middleware, routes)
│
├── k8s/                              # Kubernetes манифесты (11 файлов)
│   ├── 00-namespace.yaml             #   Namespace: umnaya
│   ├── 01-configmap.yaml             #   ConfigMap
│   ├── 02-secret.yaml                #   Secret
│   ├── 03-postgres.yaml              #   PostgreSQL
│   ├── 04-minio.yaml                 #   MinIO
│   ├── 05-kafka.yaml                 #   Kafka
│   ├── 06-api-deployment.yaml        #   API + init контейнеры
│   ├── 07-api-service.yaml           #   API Service
│   ├── 08-worker-deployment.yaml     #   Worker
│   ├── 09-nginx.yaml                 #   Nginx proxy (для MinIO)
│   └── 10-volumes.yaml               #   PV + PVC (postgres, minio, kafka)
│
├── migrations/                       # Alembic миграции
│   ├── env.py                        #   Конфигурация окружения
│   ├── script.py.mako                #   Шаблон для новых миграций
│   └── versions/                     #   Файлы миграций
│       ├── 97952d5ba82e.py           #   Initial schema (tokens, groups, photos, photo_analysis)
│       ├── 472ec77dc88b.py           #   Добавлены dominant_color, tags, model_version
│       └── e571cca9d7ca.py           #   model_version расширена до 100 символов
│
├── AI_artefacts/                     # Вспомогательные артефакты AI-сессий
├── grafana_data/                     # Данные Grafana (volume)
│
├── .env                              # Локальный конфиг (не в git)
├── .env.example                      # Пример конфига
├── .dockerignore
├── .gitignore
│
├── requirements.txt                  # Зависимости Python
├── Dockerfile                        # Сборка образа
├── docker-compose.yml                # Локальный запуск всех сервисов
├── alembic.ini                       # Конфиг Alembic
├── analyzer.proto                    # gRPC proto контракт
├── prometheus.yml                    # Конфиг Prometheus
└── startup_guide.md                  # Инструкция по запуску (устаревшая)
```

---

## Описание модулей

### `app.core` — Ядро

Модуль общей инфраструктуры. Не зависит от бизнес-логики.

- **config.py**: загружает переменные окружения через `pydantic-settings`, предоставляет объект `settings`
- **errors.py**: иерархия исключений (`AppException` → `PhotoNotFoundError`, `InvalidFile`, `AccessDeniedError` и т.д.), единый формат ответа `ErrorResponse`
- **jwt_utils.py**: HMAC-SHA256 JWT encode/decode без внешних библиотек
- **log.py**: настройка логгера с поддержкой `request_id` через `ContextVar`
- **metrics.py**: декларация Prometheus метрик (Counter, Histogram)
- **context.py**: `ContextVar` для сквозного ID запроса

### `app.api.v1` — HTTP слой

Обработчики запросов. Только валидация и вызов сервисов.

- Используют `Depends(get_current_user)` для опциональной JWT-аутентификации
- Каждый роутер подключается в `main.py`
- Все ответы в Pydantic-схемах из `app.schemas`

### `app.services` — Бизнес-логика

- **VKAuthService**: верифицирует VK подпись (HMAC-SHA256), выдаёт JWT, сохраняет токен в БД
- **PhotoService**: загрузка (валидация → MinIO → Kafka), список, детали (с анализом и группами)
- **GroupService**: управление группами дубликатов/идентичных фото

### `app.integrations` — Интеграции

- **postgreesql.py**: Database классы для каждой сущности (CRUD с SQLAlchemy)
- **minio.py**: MinIOStorage — загрузка/скачивание/presigned URL с таймаутами и метриками
- **kafka.py**: KafkaProducer — создание топика, публикация сообщений с retry
- **metrics_db.py**: агрегация метрик из PostgreSQL в Prometheus-формате

### `app.worker` — Фоновый обработчик

Асинхронный consumer на aiokafka:

1. Читает сообщение из Kafka
2. Захватывает фото (atomic UPDATE)
3. Скачивает оригинал из MinIO
4. Вызывает gRPC анализатор (с retry)
5. Вычисляет SHA256 и перцептивный хеш
6. Генерирует preview через Pillow
7. Сохраняет результаты в БД
8. Проверяет дубликаты и идентичные фото
