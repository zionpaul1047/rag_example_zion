from app.services.document_loader import load_documents
from app.services.chunker import split_documents
from app.core.settings import settings

documents = load_documents(settings.RAW_DOCS_DIR)
chunks = split_documents(documents)

print("CHUNK_SIZE =", settings.CHUNK_SIZE)
print("CHUNK_OVERLAP =", settings.CHUNK_OVERLAP)
print("전체 청크 개수:", len(chunks))

for chunk in chunks[:20]:
    print("-----")
    print("source:", chunk["source"])
    print("file_type:", chunk.get("file_type"))
    print("chunk_index:", chunk["chunk_index"])
    print("content preview:")
    print(chunk["content"][:300])
    print()