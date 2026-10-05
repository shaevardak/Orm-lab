"""Лаб. №3. Запуск: python manage.py lab3 {bulk|race|isolation}
race и isolation осмысленны на PostgreSQL (USE_PG=1)."""
import threading
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from hr.models import Department, Employee

THREADS = 10


# ---------- Bulk ----------
def bulk(out):
    dept = Department.objects.first()
    Employee.objects.filter(name__startswith="Bulk").delete()

    t = time.perf_counter()
    for i in range(20_000):
        Employee(department=dept, name=f"Bulk-save {i}", salary=Decimal(300000)).save()
    t_save = time.perf_counter() - t
    Employee.objects.filter(name__startswith="Bulk").delete()

    t = time.perf_counter()
    Employee.objects.bulk_create(
        [Employee(department=dept, name=f"Bulk-bulk {i}", salary=Decimal(300000)) for i in range(20_000)])
    t_bulk = time.perf_counter() - t
    Employee.objects.filter(name__startswith="Bulk").delete()

    out.write(f"| Способ        | Время, с |\n| save() в цикле | {t_save:8.2f} |\n| bulk_create    | {t_bulk:8.2f} |")


# ---------- Race condition ----------
def run_threads(target, emp_id):
    ts = [threading.Thread(target=target, args=(emp_id,)) for _ in range(THREADS)]
    for t in ts: t.start()
    for t in ts: t.join()


def no_lock(emp_id):
    # Lost Update: читаем -> думаем -> пишем
    e = Employee.objects.get(pk=emp_id)
    time.sleep(0.01)
    e.salary += 1
    e.save()
    connection.close()


def optimistic(emp_id):
    # Повторяем, пока версия не совпала
    while True:
        e = Employee.objects.get(pk=emp_id)
        time.sleep(0.01)
        updated = Employee.objects.filter(pk=emp_id, version=e.version).update(
            salary=e.salary + 1, version=e.version + 1)
        if updated:
            break
    connection.close()


def pessimistic(emp_id):
    with transaction.atomic():
        e = Employee.objects.select_for_update().get(pk=emp_id)  # SELECT ... FOR UPDATE
        time.sleep(0.01)
        e.salary += 1
        e.save()
    connection.close()


def race(out):
    emp = Employee.objects.first()
    if connection.vendor != "postgresql":
        out.write("SQLite не поддерживает блокировку строк (select_for_update) — запустите с USE_PG=1")
        return
    for name, fn in (("без блокировки", no_lock), ("optimistic", optimistic), ("pessimistic", pessimistic)):
        Employee.objects.filter(pk=emp.pk).update(salary=1000, version=0)
        t = time.perf_counter()
        run_threads(fn, emp.pk)
        elapsed = time.perf_counter() - t
        final = Employee.objects.get(pk=emp.pk).salary
        out.write(f"{name:15} ожидали {1000 + THREADS}, получили {final}, время {elapsed:.2f} с")


# ---------- Isolation ----------
def isolation(out):
    if connection.vendor != "postgresql":
        out.write("Нужен PostgreSQL: USE_PG=1")
        return
    emp = Employee.objects.first()
    for level in ("READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"):
        Employee.objects.filter(pk=emp.pk).update(salary=1000)
        seen = {}

        def reader():
            with transaction.atomic():
                with connection.cursor() as c:
                    c.execute(f"SET TRANSACTION ISOLATION LEVEL {level}")
                seen["first"] = Employee.objects.get(pk=emp.pk).salary
                time.sleep(0.5)
                seen["second"] = Employee.objects.get(pk=emp.pk).salary
            connection.close()

        def writer():
            time.sleep(0.2)
            Employee.objects.filter(pk=emp.pk).update(salary=2000)
            connection.close()

        a, b = threading.Thread(target=reader), threading.Thread(target=writer)
        a.start(); b.start(); a.join(); b.join()
        kind = "Non-repeatable read" if seen["first"] != seen["second"] else "чтение стабильно"
        out.write(f"{level:16} 1-е чтение={seen['first']}, 2-е={seen['second']} -> {kind}")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("mode", choices=["bulk", "race", "isolation"])

    def handle(self, *args, **opts):
        {"bulk": bulk, "race": race, "isolation": isolation}[opts["mode"]](self.stdout)
