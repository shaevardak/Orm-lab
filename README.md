# ORM Lab (Django) — Company → Department → Employee

## Запуск
    pip install -r requirements.txt
    python manage.py makemigrations hr
    python manage.py migrate
    python manage.py seed 1000          # лаб. 1 (500–1000 записей)

## Лаб. №1 (N+1)
    SQL_LOG=1 python manage.py lab1               # до: 1 + 2N запросов
    SQL_LOG=1 python manage.py lab1 --optimized   # после: 1 запрос

## Лаб. №2 (ORM vs Raw SQL)
    python manage.py seed 20000
    python manage.py lab2

## Лаб. №3
    python manage.py lab3 bulk
    # для race/isolation запустите PostgreSQL:
    USE_PG=1 python manage.py migrate && USE_PG=1 python manage.py seed 1000
    USE_PG=1 python manage.py lab3 race
    USE_PG=1 python manage.py lab3 isolation
    python manage.py sqlmigrate hr 0001           # аудит миграции: FOREIGN KEY, INDEX
