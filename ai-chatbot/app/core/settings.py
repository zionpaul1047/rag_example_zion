import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT")
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")

    ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


settings = Settings()