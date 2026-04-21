from app.services.rag_service import ask_rag


def ask_llm(user_message: str) -> dict:
    return ask_rag(user_message)