import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "dev-key"
DEBUG = True
INSTALLED_APPS = ["hr"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# По умолчанию SQLite. Для лаб. №3 (isolation, select_for_update) задайте USE_PG=1
if os.environ.get("USE_PG"):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("PG_NAME", "orm_lab"),
        "USER": os.environ.get("PG_USER", "postgres"),
        "PASSWORD": os.environ.get("PG_PASSWORD", "postgres"),
        "HOST": os.environ.get("PG_HOST", "localhost"),
        "PORT": os.environ.get("PG_PORT", "5432"),
    }}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                             "NAME": BASE_DIR / "db.sqlite3"}}

# SQL-логирование (задание 3 лаб. №1): все запросы пишутся в консоль
LOGGING = {
    "version": 1,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django.db.backends": {
        "handlers": ["console"],
        "level": "DEBUG" if os.environ.get("SQL_LOG") else "INFO"}},
}
