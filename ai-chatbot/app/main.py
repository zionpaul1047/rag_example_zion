from fastapi import FastAPI

from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.services.chat_history_service import setup_chat_db
from app.services.document_registry_service import setup_document_registry

app = FastAPI(title="AI Chatbot")


@app.on_event("startup")
def on_startup():
    setup_chat_db()
    setup_document_registry()


app.include_router(chat_router)
app.include_router(upload_router)