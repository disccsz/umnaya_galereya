# API

!!! tip "Попробуйте интерактивную документацию"

    Запустите сервис и откройте в браузере:

    | Ссылка | Описание |
    |--------|----------|
    | [ReDoc](http://localhost:8000/redoc) | Элегантная читаемая документация |
    | [Swagger UI](http://localhost:8000/docs) | Интерактивная песочница — можно отправлять запросы прямо из браузера |
    | [/openapi.json](http://localhost:8000/openapi.json) | OpenAPI 3.0 spec в формате JSON |

---

## Аутентификация

### VK Mini Apps Authentication

Сервис использует схему аутентификации VK Mini Apps. Клиент отправляет параметры запуска
VK и подпись (`sign`). Сервер верифицирует подпись с помощью `VK_SECRET_KEY` и выдаёт JWT.

```
Authorization: Bearer <jwt_token>
```

Токен необязателен — без него доступны только публичные фото/группы.

---

## Эндпоинты

### POST /api/v1/photo/auth — Аутентификация VK

VK подпись проверяется HMAC-SHA256. При успехе возвращается JWT для последующих запросов.

**Request body:**

```json
{
  "vk_user_id": "123456789",
  "vk_app_id": "987654",
  "sign": "base64url_hmac_signature",
  "vk_access_token_settings": "...",
  "vk_are_notifications_enabled": "1",
  "vk_is_app_user": "1",
  "vk_language": "ru",
  "vk_platform": "desktop_web"
}
```

Все поля `vk_*` опциональны (кроме `vk_user_id`), `sign` обязателен.

**Response `200`:**

```json
{
  "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Ошибки:**

| Код    | Статус | Описание               |
|--------|--------|------------------------|
| `MISSING_PARAMETER` | 400 | Не указан vk_user_id/app_id/sign |
| `ACCESS_DENIED`     | 403 | Неверная подпись       |

---

### POST /api/v1/photos/ — Загрузить фото

Принимает файл, сохраняет в MinIO и ставит в очередь на анализ.

**Request:** `multipart/form-data`

| Параметр | Тип    | Описание                          |
|----------|--------|-----------------------------------|
| `photo`  | File   | Файл изображения (JPEG/PNG, ≤3MB)|

**Headers:**

| Параметр         | Описание                              |
|------------------|---------------------------------------|
| `Authorization`  | `Bearer <jwt>` (опционально, для приватных фото) |

**Response `202`:**

```json
{
  "photo_id": "p_a1b2c3d4e5f6",
  "status": "pending",
  "message": "Фото приняты в асинхронную обработку"
}
```

**Ошибки:**

| Код    | Статус | Описание               |
|--------|--------|------------------------|
| `INVALID_FILE_TYPE` | 415 | Только JPEG/PNG        |
| `FILE_TOO_LARGE`    | 413 | Файл больше 3MB        |

---

### GET /api/v1/photos/ — Список фото

Возвращает все фото (публичные — если без токена, свои — если с токеном).

**Headers:**

| Параметр         | Описание                              |
|------------------|---------------------------------------|
| `Authorization`  | `Bearer <jwt>` (опционально)          |

**Response `200`:**

```json
{
  "photos": [
    {
      "photo_id": "p_a1b2c3d4e5f6",
      "status": "done",
      "original_image_url": "https://minio.example.com/...",
      "preview_image_url": "https://minio.example.com/...",
      "created_at": "2026-07-23T12:00:00Z",
      "groups_ids": ["uuid-group-1"]
    }
  ]
}
```

---

### GET /api/v1/photos/{id} — Детали фото

**Headers:**

| Параметр         | Описание                              |
|------------------|---------------------------------------|
| `Authorization`  | `Bearer <jwt>` (опционально)          |

**Response `200`:**

```json
{
  "photo_id": "p_a1b2c3d4e5f6",
  "status": "done",
  "faces_count": 2,
  "eyes_closed_count": 0,
  "is_blurred": false,
  "blur_score": 12.5,
  "duplicate_group_id": "uuid-dup-group",
  "identity_group_id": null,
  "quality_metric": 242,
  "tags": ["portrait", "indoor"],
  "created_at": "2026-07-23T12:00:00Z"
}
```

**Ошибки:**

| Код    | Статус | Описание               |
|--------|--------|------------------------|
| `PHOTO_NOT_FOUND` | 404 | Фото не найдено        |
| `ACCESS_DENIED`   | 403 | Доступ к приватному фото запрещён |

---

### GET /api/v1/photos/{id}/content — Контент фото

Возвращает presigned URL для доступа к оригиналу и превью.

**Headers:**

| Параметр         | Описание                              |
|------------------|---------------------------------------|
| `Authorization`  | `Bearer <jwt>` (опционально)          |

**Response `200`:**

```json
{
  "photo_id": "p_a1b2c3d4e5f6",
  "image_preview_url": "https://minio.example.com/preview.jpg?...",
  "image_url": "https://minio.example.com/original.jpg?..."
}
```

---

### GET /api/v1/duplicate-groups/ — Список групп дубликатов

**Headers:**

| Параметр         | Описание                              |
|------------------|---------------------------------------|
| `Authorization`  | `Bearer <jwt>` (опционально)          |

**Response `200`:**

```json
{
  "duplicate_groups": [
    {
      "id_string": "uuid-group-1",
      "is_identity_group": false,
      "created_at": "2026-07-23T12:00:00Z",
      "photos_count": 3
    }
  ]
}
```

---

### GET /api/v1/duplicate-groups/{id} — Детали группы

**Headers:**

| Параметр         | Описание                              |
|------------------|---------------------------------------|
| `Authorization`  | `Bearer <jwt>` (опционально)          |

**Response `200`:**

```json
{
  "id_string": "uuid-group-1",
  "is_identity_group": false,
  "created_at": "2026-07-23T12:00:00Z",
  "photos": [
    {
      "photo_id": "p_a1b2c3d4e5f6",
      "is_best": true,
      "quality_metric": 242,
      "faces_count": 2,
      "is_blurred": false
    }
  ]
}
```

Лучшее фото в группе (`is_best: true`) определяется по максимальному `quality_metric`.

---

### GET /healthz — Health check

```json
{"status": "ok"}
```

### GET /readyz — Readiness check

Проверяет PostgreSQL и MinIO.

```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "storage": "ok"
  }
}
```

При недоступности — `503`:

```json
{
  "status": "unavailable",
  "checks": {
    "database": "timeout",
    "storage": "ok"
  }
}
```

### GET /metrics — Prometheus метрики

См. страницу [Метрики](metrics.md).

---

## Статусы фото

| Статус       | Описание                                  |
|--------------|-------------------------------------------|
| `uploading`  | Файл загружается в хранилище              |
| `pending`    | Файл загружен, ожидает обработки          |
| `processing` | Активно обрабатывается worker-ом          |
| `done`       | Анализ завершён успешно                   |
| `failed`     | Анализ не удался после всех попыток       |

---

## Формат ошибок

Все ошибки возвращаются в едином формате:

```json
{
  "error": {
    "code": "PHOTO_NOT_FOUND",
    "message": "Photo 'p_abc123' not found",
    "field": null,
    "details": {
      "photo_id": "p_abc123"
    }
  },
  "request_id": "a1b2c3d4e5f6"
}
```

| Поле        | Тип     | Описание                              |
|-------------|---------|---------------------------------------|
| `code`      | string  | Код ошибки (машинно-читаемый)         |
| `message`   | string  | Сообщение для человека                |
| `field`     | string? | Поле, вызвавшее ошибку (для 400)      |
| `details`   | dict?   | Дополнительная информация             |
| `request_id`| string? | ID запроса для трейсинга              |

**Коды ошибок:**

| Код                       | Статус | HTTP код            |
|---------------------------|--------|---------------------|
| `VALIDATION_ERROR`        | 400    | Bad Request         |
| `MISSING_PARAMETER`       | 400    | Bad Request         |
| `INVALID_FILE_TYPE`       | 415    | Unsupported Media   |
| `FILE_TOO_LARGE`          | 413    | Content Too Large   |
| `UNAUTHORIZED`            | 401    | Unauthorized        |
| `ACCESS_DENIED`           | 403    | Forbidden           |
| `PRIVATE_PHOTO`           | 403    | Forbidden           |
| `PHOTO_NOT_FOUND`         | 404    | Not Found           |
| `GROUP_NOT_FOUND`         | 404    | Not Found           |
| `DATABASE_ERROR`          | 503    | Service Unavailable |
| `STORAGE_UNAVAILABLE`     | 503    | Service Unavailable |
