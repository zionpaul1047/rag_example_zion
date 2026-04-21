from fastapi import APIRouter
from app.services.connection_service import check_postgres, check_elasticsearch

router = APIRouter()


@router.get("/health")
def health_check():
    postgres_version = check_postgres()
    elastic_version = check_elasticsearch()

    return {
        "status": "ok",
        "postgres": postgres_version,
        "elasticsearch": elastic_version
    }