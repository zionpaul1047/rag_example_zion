from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=50
    )

    chunks = []

    for doc in documents:
        texts = splitter.split_text(doc["content"])

        for idx, text in enumerate(texts, start=1):
            chunks.append({
                "source": doc["source"],
                "chunk_index": idx,
                "content": text
            })

    return chunks