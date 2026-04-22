from app.services.document_loader import load_documents
from app.core.settings import settings

documents = load_documents(settings.RAW_DOCS_DIR)

print("문서 개수:", len(documents))

for doc in documents:
    print("-----")
    print("source:", doc["source"])
    print("file_type:", doc["file_type"])
    print("content preview:")
    print(doc["content"][:500])
    print()