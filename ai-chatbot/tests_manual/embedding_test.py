from app.core.settings import settings
from app.services.embedding_service import embed_text

sample_query = "TV 화면이 안 나와요"
sample_doc = "TV 화면이 나오지 않을 경우 전원 케이블과 HDMI 연결 상태를 확인하세요."

print("EMBEDDING_PROVIDER =", settings.EMBEDDING_PROVIDER)
print("BGE_MODEL_NAME =", settings.BGE_MODEL_NAME)
print()

query_vector = embed_text(sample_query, is_query=True)
doc_vector = embed_text(sample_doc, is_query=False)

print("query embedding length:", len(query_vector))
print("doc embedding length:", len(doc_vector))
print("query first 5:", query_vector[:5])
print("doc first 5:", doc_vector[:5])