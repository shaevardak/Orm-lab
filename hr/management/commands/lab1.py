"""Лаб. №1: N+1. Запуск: python manage.py lab1 [--optimized]"""
import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import CaptureQueriesContext
from hr.models import Employee


def naive():
    # АНТИ-ПАТТЕРН: на каждого сотрудника уходит 2 доп. запроса (department, company)
    rows = []
    for e in Employee.objects.all():
        rows.append((e.name, e.department.name, e.department.company.name))
    return rows


def optimized():
    # Оптимизация: один JOIN-запрос
    rows = []
    for e in Employee.objects.select_related("department__company"):
        rows.append((e.name, e.department.name, e.department.company.name))
    return rows


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--optimized", action="store_true")

    def handle(self, *args, **opts):
        func = optimized if opts["optimized"] else naive
        with CaptureQueriesContext(connection) as ctx:
            start = time.perf_counter()
            rows = func()
            elapsed = (time.perf_counter() - start) * 1000
        self.stdout.write(f"Режим: {func.__name__}")
        self.stdout.write(f"Строк: {len(rows)}")
        self.stdout.write(f"Запросов к БД: {len(ctx)}")
        self.stdout.write(f"Время: {elapsed:.1f} мс")
        for q in ctx.captured_queries[:3]:
            self.stdout.write(f"  [{q['time']}s] {q['sql'][:150]}")
