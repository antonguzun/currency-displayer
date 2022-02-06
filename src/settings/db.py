from src.settings.base import env

DB_URL = env.str("DB_URL")
DB_URL_TEST = env.str(
    "DB_URL_TEST", default="postgres://postgres:dbpass@0.0.0.0:5432/db"
)
DB_QUERY_TIMEOUT = env.int("DB_QUERY_TIMEOUT", default=1)
