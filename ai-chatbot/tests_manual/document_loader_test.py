from app.services.document_loader import load_documents
from app.core.settings import settings

documents = load_documents(settings.RAW_DOCS_DIR)

print("OCR_ENABLED =", settings.OCR_ENABLED)
print("OCR_MIN_TEXT_LENGTH =", settings.OCR_MIN_TEXT_LENGTH)
print("문서 개수:", len(documents))

for doc in documents:
    print("-----")
    print("source:", doc.get("source"))
    print("file_type:", doc.get("file_type"))
    print("used_ocr:", doc.get("used_ocr"))
    print("content preview:")
    print(doc.get("content", "")[:500])
    print()