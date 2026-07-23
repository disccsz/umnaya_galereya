# Архитектура

## C4 Component — компоненты API

```mermaid
C4Component
  title Component diagram — Photo API

  Container_Boundary(api, "Photo API") {
    Component(routes, "API Routes", "FastAPI routers", "Обработка входящих HTTP запросов")
    Component(auth, "Auth Service", "VKAuthService", "Верификация VK подписи, выдача JWT")
    Component(photos, "Photo Service", "PhotoService", "Загрузка, список, детали фото")
    Component(groups, "Group Service", "GroupService", "Группы дубликатов и идентичных фото")
    Component(db, "Database Layer", "PhotoDatabase / GroupDatabase / TokenDatabase", "SQLAlchemy async сессии")
    Component(storage, "Storage Layer", "MinIOStorage", "Работа с S3 хранилищем")
    Component(kafka_prod, "Kafka Producer", "KafkaProducer", "Публикация событий")
    Component(metrics, "Metrics", "Prometheus client", "HTTP + бизнес метрики")
    Component(errors, "Error Handler", "AppException", "Централизованная обработка ошибок")
    Component(config, "Config", "pydantic-settings", "Загрузка переменных окружения")
  }

  Rel(client, routes, "HTTP", "")
  Rel(routes, auth, "call", "")
  Rel(routes, photos, "call", "")
  Rel(routes, groups, "call", "")
  Rel(photos, db, "SQLAlchemy", "")
  Rel(photos, storage, "MinIO SDK", "")
  Rel(photos, kafka_prod, "aiokafka", "")
  Rel(groups, db, "SQLAlchemy", "")
  Rel(auth, db, "SQLAlchemy", "")
  Rel(routes, metrics, "record", "")
```

---

## ER Diagram — база данных

```mermaid
erDiagram
  tokens {
    string data_token PK "Первичный ключ"
    string auth_token UK "JWT токен"
    string vk_owner_user_id "ID пользователя VK"
    datetime created_at_time "Дата создания"
    datetime expires_at "Дата истечения"
  }

  groups {
    int id PK "Первичный ключ"
    string id_string UK "UUID группы"
    string owner_data_token FK "Владелец (для приватных групп)"
    datetime created_at "Дата создания"
    bool is_identity_group "Группа идентичных фото"
    bool is_private "Приватная группа"
    string standart_hash "Хеш (SHA256/phash) для поиска"
  }

  photos {
    int id PK "Первичный ключ"
    string id_string UK "UUID фото"
    string object_key "Ключ объекта в MinIO"
    string preview_key "Ключ превью в MinIO"
    datetime load_time "Время загрузки"
    bigint photo_size "Размер файла в байтах"
    enum status "Статус: uploading/pending/processing/done/failed"
    int attempts "Количество попыток анализа"
    int last_error_code "Код последней ошибки"
    string last_error_message "Сообщение последней ошибки"
    bool is_private "Приватное фото"
    string owner_data_token FK "Владелец"
    int duplicate_group_id FK "Группа дубликатов"
    int identity_photo_group_id FK "Группа идентичных фото"
  }

  photo_analysis {
    int photo_id PK, FK "ID фото (1 к 1)"
    int faces_count "Количество лиц"
    int eyes_closed_count "Количество закрытых глаз"
    bool is_blurred "Размыто?"
    float blur_score "Оценка размытия"
    int quality_metric "Метрика качества (0-255)"
    int light_level "Уровень освещения"
    string dominant_color "Доминантный цвет (HEX)"
    string tags "Теги (JSON)"
    string model_version "Версия модели анализатора"
    string perceptual_hash "Перцептивный хеш (phash)"
    string sha256_hash "SHA256 хеш"
    datetime analysis_at "Время анализа"
  }

  tokens ||--o{ photos : "владеет"
  tokens ||--o{ groups : "владеет"
  groups ||--o{ photos : "содержит дубликаты"
  groups ||--o{ photos : "содержит идентичные"
  photos ||--|| photo_analysis : "имеет анализ"
```

---

## Sequence — поток загрузки и анализа фото

```mermaid
sequenceDiagram
  participant Client as Пользователь
  participant API as Photo API
  participant MinIO as MinIO Storage
  participant Kafka as Kafka
  participant Worker as Photo Worker
  participant Analyzer as gRPC Analyzer
  participant DB as PostgreSQL

  Client->>API: POST /api/v1/photos/ (file)
  activate API

  API->>API: Валидация (тип, размер, магия)
  API->>DB: INSERT photos (status=uploading)
  API->>MinIO: PUT original.jpg
  API->>DB: UPDATE status=pending
  API->>Kafka: PUBLISH photo-uploaded

  API-->>Client: 202 Accepted {photo_id, status:pending}
  deactivate API

  activate Worker
  Worker->>Kafka: CONSUME photo-uploaded
  Worker->>DB: UPDATE status=processing, attempts+1
  Worker->>MinIO: GET original.jpg
  Worker->>Analyzer: gRPC AnalyzePhoto()

  alt Успешный анализ
    Analyzer-->>Worker: faces_count, blur_score, phash, tags...
    Worker->>Worker: SHA256 хеш
    Worker->>Worker: Перцептивный хеш
    Worker->>Worker: Генерация preview.jpg
    Worker->>MinIO: PUT preview.jpg
    Worker->>DB: INSERT photo_analysis
    Worker->>DB: UPDATE status=done, preview_key

    Worker->>DB: Поиск идентичных фото (SHA256)
    alt Найдено совпадение
      Worker->>DB: Привязать к группе идентичных
    end

    Worker->>DB: Поиск дубликатов (phash, distance<20)
    alt Найдено совпадение
      Worker->>DB: Привязать к группе дубликатов
    end

  else Ошибка анализа
    Worker->>DB: UPDATE status=failed, error_message
  end
  deactivate Worker
```

---

## Описание потока данных

### Загрузка фото

1. Клиент отправляет файл через `POST /api/v1/photos/`
2. API валидирует: тип (`image/jpeg`, `image/png`), размер (≤3 МБ), magic bytes
3. API сохраняет запись в PostgreSQL со статусом `uploading`
4. API загружает файл в MinIO по ключу `photos/{id}/original.{ext}`
5. API обновляет статус на `pending`
6. API публикует событие в Kafka (топик `photo-uploaded`)
7. Клиенту возвращается `202 Accepted`

### Анализ фото (Worker)

1. Worker потребляет событие из Kafka
2. Worker захватывает фото (optimistic lock: `UPDATE ... WHERE status=pending`)
3. Worker читает оригинал из MinIO
4. Worker вызывает внешний gRPC анализатор:
    - Детекция лиц (`faces_count`)
    - Детекция закрытых глаз (`eyes_closed_count`)
    - Оценка размытия (`is_blurred`, `blur_score`)
    - Перцептивный хеш (`perceptual_hash`)
    - Доминантный цвет (`dominant_color`)
    - Теги (`tags`)
    - Версия модели (`model_version`)
5. Worker вычисляет SHA256 и перцептивный хеш (своя реализация)
6. Worker генерирует preview (JPEG, max 800px width)
7. Worker загружает preview в MinIO
8. Worker сохраняет все результаты анализа в БД
9. Worker проверяет дубликаты и идентичные фото:
    - **Идентичные**: точное совпадение SHA256 → общая группа `identity`
    - **Дубликаты**: перцептивный хеш с расстоянием Хэмминга < 20 → общая группа `duplicate`
10. Если не удалось связаться с анализатором — до 4 повторных попыток
11. После 5-й неудачи — статус `failed`
