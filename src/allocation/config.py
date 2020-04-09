import os


def get_api_url() -> str:
    host = os.environ.get("API_HOST", "localhost")
    port = 5000
    return f"http://{host}:{port}"


def get_postgres_uri() -> str:
    host, port, db_name = "localhost", 5432, "allocation"

    heroku_url = os.environ.get("DATABASE_URL", None)
    default_url = f"postgresql://{host}:{port}/{db_name}"
    return heroku_url if heroku_url else default_url
