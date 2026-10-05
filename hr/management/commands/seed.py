import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from hr.models import Company, Department, Employee


class Command(BaseCommand):
    help = "Заполнить БД тестовыми данными: python manage.py seed [кол-во сотрудников]"

    def add_arguments(self, parser):
        parser.add_argument("n", nargs="?", type=int, default=1000)

    def handle(self, *args, **opts):
        Employee.objects.all().delete()
        Department.objects.all().delete()
        Company.objects.all().delete()
        companies = [Company.objects.create(name=f"Company {i}") for i in range(5)]
        depts = [Department.objects.create(company=c, name=f"Dept {c.id}-{j}")
                 for c in companies for j in range(4)]
        Employee.objects.bulk_create([
            Employee(department=random.choice(depts), name=f"Employee {i}",
                     salary=Decimal(random.randint(200_000, 1_500_000)))
            for i in range(opts["n"])
        ])
        self.stdout.write(self.style.SUCCESS(
            f"{len(companies)} компаний, {len(depts)} департаментов, {opts['n']} сотрудников"))
