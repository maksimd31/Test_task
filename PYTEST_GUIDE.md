# Руководство по тестированию (pytest + pytest-cov)

## 1. Что уже настроено
Файл `pytest.ini` содержит предустановленные опции:
- `DJANGO_SETTINGS_MODULE=Test_task.settings` — автоматическая загрузка настроек Django.
- Шаблоны файлов тестов: `test_*.py`, `*_tests.py`.
- Покрытие кода: `--cov=apps` + отчёты: терминальный (`term-missing`) и HTML (`htmlcov/`).
- Порог покрытия: `--cov-fail-under=80` (упадёт, если меньше 80%).
- Ускорение: `--reuse-db` (переиспользование тестовой БД), `--nomigrations` (пропуск применения миграций — Django создаёт схему напрямую по моделям).
- Более строгий режим: `--strict-markers`, `--strict-config`.

Маркировки (markers):
- `@pytest.mark.slow`
- `@pytest.mark.integration`
- `@pytest.mark.unit`
- `@pytest.mark.celery`
- `@pytest.mark.cache`

## 2. Базовый запуск
```bash
pytest -q            # тихий вывод
pytest               # подробный вывод (включая addopts из pytest.ini)
```

## 3. Покрытие кода
После запуска формируется:
- Терминальный отчёт c пропущенными строками.
- HTML отчёт в директории `htmlcov/` → открыть `htmlcov/index.html` браузером.

Перегенерация без кэша pytest:
```bash
pytest --cache-clear
```

Запуск только покрытия (уже в addopts):
```bash
pytest --cov=apps --cov-report=term-missing
```

Покрытие для конкретного модуля:
```bash
pytest apps/orders/tests/test_services_and_tasks.py --cov=apps/orders/services.py --cov-report=term-missing
```

## 4. Работа с маркерами
Запуск без «медленных» тестов:
```bash
pytest -m "not slow"
```
Только интеграционные:
```bash
pytest -m integration
```
Только кэш-тесты:
```bash
pytest -m cache
```
Комбинация:
```bash
pytest -m "integration and not slow"
```

## 5. Запуск отдельных тестов
По имени файла:
```bash
pytest apps/products/tests/test_api.py
```
По классу/функции:
```bash
pytest apps/orders/tests/test_services_and_tasks.py::test_create_order_service_success
```
С ключевым словом (pattern):
```bash
pytest -k "pdf and not retry"
```

## 6. Диагностика падений
Показать полную трассировку:
```bash
pytest -vv --maxfail=1 --tb=long
```
Повторить упавшие из последнего запуска:
```bash
pytest --last-failed
```
Запустить только впервые упавшие (если были xfails):
```bash
pytest --failed-first
```

## 7. Локальный debug
Запуск с pdb при первом падении:
```bash
pytest -x --pdb
```
Поставить точку останова внутри теста:
```python
import pdb; pdb.set_trace()
```

## 8. Изменение порога покрытия
Во временном запуске (например, 85%):
```bash
pytest --cov-fail-under=85
```
Постоянно — измените значение в `pytest.ini` (опция `--cov-fail-under`).

## 9. Генерация дополнительных отчётов (для CI)
XML-отчёт (подходит для GitLab/Jenkins/SonarQube):
```bash
pytest --cov=apps --cov-report=xml:coverage.xml
```
Можно комбинировать:
```bash
pytest --cov=apps --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html
```

## 10. Ускорение
- Уже включены `--reuse-db` и `--nomigrations`.
- Дополнительно можно установить `pytest-xdist` и запускать: `pytest -n auto`.
- Отключить покрытие для чистого замера скорости:
```bash
pytest -q --no-cov
```

## 11. Исключение файлов из покрытия
Исключения `.coveragerc` (если понадобится):
```ini
[run]
omit =
    */migrations/*
    */apps.py
```
И затем:
```bash
pytest --cov=apps --cov-config=.coveragerc
```

## 12. Типичные ошибки
| Симптом | Причина | Решение |
|---------|---------|---------|
| FAIL Coverage < 80% | Недостаточно тестов | Добавить тесты / снизить порог (временно) |
| ImproperlyConfigured | DJANGO_SETTINGS_MODULE не найден | Проверить pytest.ini |
| Database locked | Параллельные процессы / SQLite | Перезапуск, PostgreSQL в CI |
| NoReverseMatch | Удалён/переименован URL | Обновить тест или вернуть алиас |

## 13. Рекомендации по тестам
- Изолируйте бизнес-логику в сервисах — легче покрывать.
- Используйте фабрики (factory-boy) вместо ручного создания данных.
- Для Celery — `task_always_eager=True` уже включается фикстурой.
- Внешние запросы мокать (`unittest.mock.patch`).

## 14. Быстрый чек-лист перед коммитом
- Все тесты зелёные: `pytest -q`.
- Покрытие не ниже порога.
- htmlcov просмотрен для новых модулей.
- Нет отладочных принтов / pdb.

## 15. Полезные однострочники
```bash
# Топ 10 самых длинных файлов без полного покрытия (примерный подход):
pytest --cov=apps --cov-report=term-missing | sed -n '/apps\//p' | sort -k3 -nr | head -10

# Быстрый прогон только новых/изменённых файлов (git):
pytest $(git diff --name-only HEAD | grep '^apps/.\+test_.*py$' || echo '')
```

---

