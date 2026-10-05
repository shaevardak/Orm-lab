from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="departments")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Employee(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="employees")
    name = models.CharField(max_length=100)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    version = models.IntegerField(default=0)  # для оптимистичной блокировки (лаб. №3)

    class Meta:
        indexes = [models.Index(fields=["salary"])]  # чтобы изучить индексы в миграции

    def __str__(self):
        return self.name
