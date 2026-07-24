# Метрики Prometheus

Эндпоинт: `GET /metrics` (порт `8000`)

Prometheus настроен на сбор метрик в `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'photo-api'
    scrape_interval: 15s
    metrics_path: '/metrics'
    static_configs:
      - targets: ['api:8000']
```

---

## Метрики приложения

Определены в `app/core/metrics.py`.

### `photos_uploaded_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Help  | Total photos uploaded           |
| Labels| —                               |

Инкрементируется при успешной загрузке фото.

### `http_requests_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Help  | Total HTTP requests             |
| Labels| `method`, `path`, `status_code` |

Инкрементируется на каждый входящий HTTP запрос (middleware в `main.py:82-85`).

### `http_request_duration_seconds`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Histogram                       |
| Help  | HTTP request duration           |
| Labels| `method`, `path`, `status_code` |
| Buckets| `[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 10.0]` |

Записывает длительность каждого HTTP запроса.

### `storage_upload_errors_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Help  | MinIO upload errors             |
| Labels| `error_code`                    |

Инкрементируется при ошибках MinIO.

### `kafka_publish_errors_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Help  | Kafka publish errors            |
| Labels| `topic`                         |

Инкрементируется при ошибках публикации в Kafka.

---

## Метрики из БД

Агрегируются в `app/integrations/metrics_db.py` через прямой SQL.

### `photo_analysis_completed_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Labels| `status` ("done" / "failed")   |

Количество завершённых анализов по статусу.

### `photo_analysis_failed_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Help  | Analysis permanently failed     |

Количество фото, перешедших в статус `failed`.

### `photo_analysis_duration_seconds`

| Поле   | Значение                         |
|--------|----------------------------------|
| Тип    | Histogram                        |
| Buckets| `1, 5, 10, 30, 60, 120, +Inf`   |
| Help   | Analysis duration from upload to completion |

Гистограмма времени между `photos.load_time` и `photo_analysis.analysis_at`.

### `analyzer_grpc_errors_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Help  | Total gRPC analyzer retries     |

Вычисляется как `SUM(attempts) - COUNT(done|failed)`. Отражает количество лишних попыток,
связанных с ошибками gRPC (разница между общим числом попыток и успешно/безуспешно
обработанными фото).

### `worker_messages_processed_total`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Counter                         |
| Labels| `result` ("success" / "error")|

Количество сообщений, обработанных worker-ом.

### `consumer_lag`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Gauge                           |
| Help  | Photos waiting in queue (pending + processing) |

Количество фото, ожидающих обработки или в процессе.

### `messages_in_queue`

| Поле  | Значение                        |
|-------|---------------------------------|
| Тип   | Gauge                           |
| Help  | Photos pending                  |

Количество фото в статусе `pending`.

---

## Пример вывода `/metrics`

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/v1/photos/",status_code="200"} 42
http_requests_total{method="POST",path="/api/v1/photos/",status_code="202"} 15

# HELP photos_uploaded_total Total photos uploaded
# TYPE photos_uploaded_total counter
photos_uploaded_total 15

# HELP consumer_lag Photos waiting in queue (pending + processing)
# TYPE consumer_lag gauge
consumer_lag 3
```
