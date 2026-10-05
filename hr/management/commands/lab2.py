"""Лаб. №2: топ-3 по зарплате в департаменте + разница со средней по департаменту.
Запуск: python manage.py lab2"""
import time
import tracemalloc
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.models import Avg, F, Window
from django.db.models.functions import DenseRank
from hr.models import Employee

RAW_SQL = """
SELECT * FROM (
    SELECT e.id, e.name, d.name AS dept, e.salary,
           DENSE_RANK() OVER (PARTITION BY e.department_id ORDER BY e.salary DESC) AS rnk,
           e.salary - AVG(e.salary) OVER (PARTITION BY e.department_id) AS diff_from_avg
    FROM hr_employee e
    JOIN hr_department d ON d.id = e.department_id
) t
WHERE rnk <= 3
ORDER BY dept, rnk
"""


def orm_version():
    qs = Employee.objects.select_related("department").annotate(
        rnk=Window(DenseRank(), partition_by=[F("department_id")], order_by=F("salary").desc()),
        diff_from_avg=F("salary") - Window(Avg("salary"), partition_by=[F("department_id")]),
    )
    # Фильтр по оконной функции работает только в Django 4.2+ (генерируется подзапрос)
    return list(qs.filter(rnk__lte=3).order_by("department__name", "rnk"))


def raw_version():
    with connection.cursor() as c:
        c.execute(RAW_SQL)
        return c.fetchall()


def bench(func):
    tracemalloc.start()
    t = time.perf_counter()
    result = func()
    elapsed = (time.perf_counter() - t) * 1000
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak / 1024


class Command(BaseCommand):
    def handle(self, *args, **opts):
        self.stdout.write(f"Сотрудников в БД: {Employee.objects.count()}")
        for name, f in (("ORM", orm_version), ("Raw SQL", raw_version)):
            res, ms, kb = bench(f)
            self.stdout.write(f"{name:8} строк={len(res):3}  время={ms:8.1f} мс  пик RAM={kb:9.1f} КБ")
        # SQL, который сгенерировал ORM — для сравнения в отчёте
        qs = Employee.objects.select_related("department").annotate(
            rnk=Window(DenseRank(), partition_by=[F("department_id")], order_by=F("salary").desc()),
            diff_from_avg=F("salary") - Window(Avg("salary"), partition_by=[F("department_id")]),
        ).filter(rnk__lte=3)
        self.stdout.write("\n--- SQL от ORM ---\n" + str(qs.query))
        self.stdout.write("\n--- Raw SQL ---" + RAW_SQL)
