# Умная галерея

**Photo Analysis Service** — асинхронный сервис для загрузки, анализа и управления фотографиями с
детекцией лиц, оценкой качества, поиском дубликатов и идентичных изображений.

---

## Технологический стек

| Компонент          | Технология                        |
|--------------------|-----------------------------------|
| **API**            | FastAPI (Python 3.14)            |
| **База данных**    | PostgreSQL 16 + asyncpg          |
| **ORM**            | SQLAlchemy async                 |
| **Миграции**       | Alembic                          |
| **Объектное хранилище** | MinIO (S3-совместимое)      |
| **Очередь сообщений** | Apache Kafka                  |
| **Анализ фото**    | Внешний gRPC-сервис              |
| **Метрики**        | Prometheus + Grafana             |
| **Контейнеризация** | Docker + docker-compose         |
| **Оркестрация**    | Kubernetes (kind)                |

---

## C4 Context — системный контекст

```mermaid
C4Context
  title System Context — Умная галерея

  Person(client, "Пользователь VK", "Загружает фото, просматривает результаты анализа")

  System_Boundary(system, "Умная галерея") {
    System(api, "Photo API", "FastAPI приложение — загрузка фото, управление, аутентификация")
  }

  System_Ext(analyzer, "Analyzer gRPC", "Внешний сервис анализа фото: лица, размытие, качество")

  Rel(client, api, "HTTP (REST)", "Загружает фото, запрашивает данные")
  Rel(api, analyzer, "gRPC", "Отправляет фото на анализ через Worker")
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

---

## C4 Container — контейнеры

```mermaid
C4Container
  title Container diagram — Умная галерея

  Person(client, "Пользователь VK", "VK Mini App / API Client")

  System_Boundary(umnaya, "Умная галерея") {
    Container(api, "Photo API", "FastAPI + Uvicorn", "Обрабатывает HTTP запросы, авторизация, загрузка фото, просмотр")
    Container(worker, "Photo Worker", "Python asyncio", "Фоновый обработчик: анализ, хеширование, превью")
    ContainerDb(db, "PostgreSQL", "PostgreSQL 16", "Хранит метаданные фото, токены, группы, результаты анализа")
    Container(storage, "MinIO", "S3-совместимое хранилище", "Хранит оригиналы и превью фотографий")
    Container(kafka, "Kafka", "Apache Kafka", "Очередь событий: фото загружено → worker")
    Container(mon, "Prometheus + Grafana", "Мониторинг", "Сбор и визуализация метрик")
  }

  System_Ext(analyzer, "Analyzer gRPC", "Внешний AI-сервис анализа")

  Rel(client, api, "HTTP", "Загружает фото / запрашивает данные")
  Rel(api, storage, "MinIO SDK", "Сохраняет оригинал фото")
  Rel(api, kafka, "aiokafka", "Публикует событие photo-uploaded")
  Rel(worker, kafka, "aiokafka", "Потребляет события")
  Rel(worker, storage, "MinIO SDK", "Читает оригинал, загружает превью")
  Rel(worker, analyzer, "gRPC", "Отправляет фото на анализ")
  Rel(worker, db, "SQLAlchemy async", "Сохраняет результаты анализа")
  Rel(api, db, "SQLAlchemy async", "Читает/пишет данные")
  Rel(mon, api, "HTTP", "Собирает метрики /metrics")
  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

---

## Быстрая навигация

<div class="grid cards" markdown>

-   :material-rocket-launch: **Быстрый старт**

    Запустите проект локально или в Kubernetes за 5 минут

    [:octicons-arrow-right-24: Начать](getting-started.md)

-   :material-sitemap: **Архитектура**

    C4 диаграммы, ER диаграмма, Sequence диаграмма потока данных

    [:octicons-arrow-right-24: Смотреть](architecture.md)

-   :material-api: **API**

    Полная документация всех эндпоинтов с примерами

    [:octicons-arrow-right-24: Изучить](api.md)

-   :material-docker: **Развёртывание**

    Docker Compose и Kubernetes манифесты

    [:octicons-arrow-right-24: Развернуть](deployment.md)

-   :material-tune-variant: **Переменные окружения**

    Все конфигурационные параметры сервиса

    [:octicons-arrow-right-24: Настроить](environment.md)

-   :material-folder-open: **Структура проекта**

    Дерево файлов с описанием каждого модуля

    [:octicons-arrow-right-24: Изучить](project-structure.md)

-   :material-chart-box-outline: **Метрики**

    Prometheus метрики приложения

    [:octicons-arrow-right-24: Просмотр](metrics.md)

</div>
