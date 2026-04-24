from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.upload import router as upload_router
from app.services.chat_history_service import setup_chat_db
from app.services.document_registry_service import setup_document_registry

app = FastAPI(title="AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:7860",
        "http://127.0.0.1:7860",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    setup_chat_db()
    setup_document_registry()


app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(upload_router)