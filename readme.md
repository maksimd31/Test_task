# E-commerce API

Django REST API для управления интернет-магазином с функциями заказов, продуктов и пользователей.

## Технологический стек

- **Django 5.2.6**
- **Django REST Framework**
- **PostgreSQL / SQLite**
- **Celery + Redis**
- **Memcached (официальный backend MemcachedCache + python-memcached)**
- **JWT (simplejwt)**
- **Docker / Docker Compose**
- **ReportLab (PDF)**
- **Swagger / Redoc (drf-spectacular)**

---
## 1. Установка и запуск (Docker)

```bash
git clone <https://github.com/maksimd31/Test_task>
cd Test_task
cp .env.example .env
# Запуск всех сервисов (web, db, redis, memcached, celery, celery-beat)
docker-compose up -d --build
# Применение миграций
docker-compose exec web python manage.py migrate
# Создание суперпользователя
docker-compose exec web python manage.py createsuperuser
```
Проверка:
```bash
curl -I http://localhost:8000/api/docs/
```
Остановка:
```bash
docker-compose down
```
Очистка (с удалением volume БД):
```bash
docker-compose down -v
```

### Локальный запуск без Docker
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
# В отдельных терминалах:
celery -A Test_task worker -l info
celery -A Test_task beat -l info
```

---
## 2. Переменные окружения (.env)
| Переменная | Назначение | Пример |
|------------|-----------|--------|
| SECRET_KEY | Django secret | changeme123... |
| DEBUG | Режим отладки | False |
| ALLOWED_HOSTS | Разрешённые хосты | localhost,127.0.0.1 |
| DATABASE_URL | Подключение к БД | postgresql://user:pass@db:5432/app |
| REDIS_URL | Брокер/бэкенд Celery | redis://redis:6379/0 |
| MEMCACHED_URL | Хост Memcached | memcached:11211 |

---
## 3. Документация API
- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI JSON: http://localhost:8000/api/schema/

---
## 4. Примеры curl всех эндпоинтов

### Аутентификация
```bash
# Регистрация
curl -X POST http://localhost:8000/api/auth/register/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"u1","email":"u1@example.com","password":"StrongPass123!","password_confirm":"StrongPass123!"}'

# Логин
curl -X POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"u1@example.com","password":"StrongPass123!"}'

# Обновление access токена
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H 'Content-Type: application/json' \
  -d '{"refresh":"<refresh_token>"}'

# Профиль (GET)
curl -H 'Authorization: Bearer <access_token>' http://localhost:8000/api/auth/profile/

# Профиль (PATCH)
curl -X PATCH http://localhost:8000/api/auth/profile/ \
  -H 'Authorization: Bearer <access_token>' -H 'Content-Type: application/json' \
  -d '{"phone":"+70000000000"}'
```

### Продукты
```bash
# Список (фильтры + сортировка)
curl -H 'Authorization: Bearer <token>' "http://localhost:8000/api/products/?category=electronics&price_min=10&price_max=500&ordering=price"

# Создание (admin)
curl -X POST http://localhost:8000/api/products/ \
  -H 'Authorization: Bearer <admin_token>' -H 'Content-Type: application/json' \
  -d '{"name":"Phone","description":"Desc","price":"199.99","stock":10,"category":"electronics"}'

# Детали
curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/products/1/

# Обновление (PATCH, admin)
curl -X PATCH http://localhost:8000/api/products/1/ \
  -H 'Authorization: Bearer <admin_token>' -H 'Content-Type: application/json' \
  -d '{"price":"149.99"}'

# Удаление (admin)
curl -X DELETE http://localhost:8000/api/products/1/ \
  -H 'Authorization: Bearer <admin_token>'
```

### Заказы
```bash
# Создание заказа
curl -X POST http://localhost:8000/api/orders/ \
  -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \
  -d '{"items":[{"product_id":1,"quantity":2},{"product_id":2,"quantity":1}]}'

# Список своих заказов
curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/orders/

# Детали заказа
curl -H 'Authorization: Bearer <token>' http://localhost:8000/api/orders/5/

# Обновление статуса (PATCH)
curl -X PATCH http://localhost:8000/api/orders/5/ \
  -H 'Authorization: Bearer <token>' -H 'Content-Type: application/json' \
  -d '{"status":"shipped"}'
```

### Админ: все заказы
```bash
curl -H 'Authorization: Bearer <admin_token>' "http://localhost:8000/api/admin/orders/?status=shipped&user_id=3"
```

### Документация и схема
```bash
curl http://localhost:8000/api/schema/ -o openapi.json
```

---
## 5. Архитектура и принятые решения

### Слои
- Модели: бизнес-сущности (User, Product, Order, OrderItem).
- Сериализаторы: валидация, форматирование ответа (разделены create/read при необходимости).
- Сервисный слой (apps/orders/services.py): атомарная логика создания заказа + управление stock.
- Вьюхи: тонкие контроллеры (DRF generic CBV) + выбор сериализаторов.
- Задачи Celery: побочные эффекты (PDF, внешние уведомления). В тестовом режиме task_always_eager.

### Concurrency и целостность
- select_for_update при создании заказа гарантирует корректное уменьшение stock без гонок.
- Атомарная транзакция вокруг всей операции заказа.

### Кэширование
- Версионное кэширование (namespace version) вместо массового удаления ключей.
- Продукты: key pattern `products_list_v<version>_<querystring>` TTL=300 c.
- Заказы (детали): key pattern `order_detail_v<version>_<order_id>` TTL=60 c.
- Signals (post_save/post_delete) поднимают версию — единый массовый инвалидационный механизм.

### Асинхронные задачи
- generate_order_pdf_and_send_email: ReportLab генерирует PDF (байты в памяти), имитация email через лог.
- notify_external_api_order_shipped: POST на jsonplaceholder + retry (max_retries=3).

### Валидации
- Положительная цена, quantity.
- Уникальность product в заказе.
- Минимальная сумма заказа через settings.MIN_ORDER_AMOUNT.
- Проверка остатка stock с блокировкой.

### Безопасность и аутентификация
- JWT (access/refresh) через simplejwt.
- Все эндпоинты (кроме регистрации/логина) требуют токен.
- Обновление/просмотр заказов — только владелец или staff.

### Тестирование
- pytest + factory-boy.
- Покрытие API, кэша (hit/miss), сервисного слоя, задач Celery, конкурентного сценария stock.
- Eager задачи Celery для детерминизма.

### Почему версионный кэш
- Массовая инвалидация O(1), не нужно хранить/перебирать ключи.
- Снижение рисков утечки устаревших ключей.

### Возможные улучшения (необязательно)
- Добавить metrics / Prometheus.
- Использовать gunicorn/uvicorn в Dockerfile для prod.
- Расширить аудит логов (status transitions).

---
## 6. Политика кэширования (кратко)
- Products list: 5 мин, версия ↑ при изменениях.
- Order detail: 1 мин, версия ↑ при изменении заказа / его items / статуса.

---
## 7. Асинхронные задачи (кратко)
| Задача | Триггер | Действие |
|--------|---------|----------|
| generate_order_pdf_and_send_email | Создание заказа | Генерация PDF + лог «email» |
| notify_external_api_order_shipped | Статус -> shipped | POST внешнему API + retry |

---
## 8. Статус
- Реализованы все обязательные требования тестового задания.
- Дополнительно: версионный кэш, сервисный слой, сигнал-инвалидация, eager Celery для тестов.
