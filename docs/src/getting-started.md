# Быстрый старт

## Docker Compose

```bash
# Запуск всех сервисов
docker compose up -d

# Проверка
curl http://localhost:8000/healthz
# {"status": "ok"}
```

Сервисы и порты:

| Сервис     | Порт         | Назначение                         |
|------------|--------------|-------------------------------------|
| API        | `8000`       | REST API                           |
| PostgreSQL | `5435`       | База данных                         |
| MinIO      | `9100` (API) | S3-совместимое хранилище           |
| Kafka      | `9092`       | Очередь сообщений                   |
| Prometheus | `9090`       | Сбор метрик                         |
| Grafana    | `3000`       | Визуализация метрик                 |

## Kubernetes (kind)

```bash
# 1. Создать кластер kind
kind create cluster --name umnaya

# 2. Подготовить папки для PersistentVolume
docker exec umnaya-control-plane mkdir -p /var/lib/umnaya/{postgres,minio,kafka}

# 3. Собрать образ
docker build -t umnaya-api .

# 4. Загрузить образ в kind
kind load docker-image umnaya-api --name umnaya

# 5. Применить манифесты
kubectl apply -f k8s/

# 6. Дождаться готовности подов
kubectl get pods -n umnaya -w

# 7. Открыть доступ к API (в отдельном терминале)
kubectl port-forward -n umnaya svc/api-service 8000:8000 --address 0.0.0.0
```

## Локальный запуск (без Docker)

```bash
# 1. Установить зависимости
pip install -r requirements.txt

# 2. Настроить .env (скопировать из .env.example)
cp .env.example .env

# 3. Запустить PostgreSQL, MinIO, Kafka вручную (через Docker)
docker compose up -d postgres minio kafka

# 4. Применить миграции
alembic upgrade head

# 5. Запустить API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. (в другом терминале) Запустить Worker
python -m app.worker
```

## Пересборка при изменениях (kind)

```bash
# 1. Собрать новый образ
docker build -t umnaya-api .

# 2. Загрузить в kind
kind load docker-image umnaya-api --name umnaya

# 3. Перезапустить поды
kubectl delete pod -n umnaya -l app=api
kubectl delete pod -n umnaya -l app=worker
```

## Остановка

```bash
# Docker Compose
docker compose down

# Kubernetes
kubectl scale deployment -n umnaya --all --replicas=0
```
