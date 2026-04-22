from app.core.settings import settings

print("APP_NAME =", settings.APP_NAME)
print("APP_ENV =", settings.APP_ENV)
print("POSTGRES_HOST =", settings.POSTGRES_HOST)
print("POSTGRES_PORT =", settings.POSTGRES_PORT)
print("POSTGRES_DB =", settings.POSTGRES_DB)
print("POSTGRES_USER =", settings.POSTGRES_USER)
print("OPENAI_CHAT_MODEL =", settings.OPENAI_CHAT_MODEL)
print("OPENAI_EMBEDDING_MODEL =", settings.OPENAI_EMBEDDING_MODEL)
print("CHUNK_SIZE =", settings.CHUNK_SIZE)
print("CHUNK_OVERLAP =", settings.CHUNK_OVERLAP)
print("TOP_K_RETRIEVAL =", settings.TOP_K_RETRIEVAL)
print("TOP_N_CONTEXT =", settings.TOP_N_CONTEXT)