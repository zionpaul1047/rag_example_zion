from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.settings import settings


def split_documents(documents: list[dict]) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    chunks = []

    for doc in documents:
        texts = splitter.split_text(doc["content"])

        for idx, text in enumerate(texts, start=1):
            chunks.append({
                "source": doc["source"],
                "file_type": doc.get("file_type", "unknown"),
                "chunk_index": idx,
                "content": text
            })

    return chunks