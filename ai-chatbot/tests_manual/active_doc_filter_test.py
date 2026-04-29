from app.services.document_registry_service import get_active_managed_document_sources
from app.services.rag_service import ask_rag

print("=== active managed sources ===")
print(get_active_managed_document_sources())
print()

result = ask_rag(
    "TV 화면이 안 나와요",
    llm_provider="openai",
)

print("conversation_id:", result["conversation_id"])
print("eval_result:", result.get("eval_result"))
print("sources:")
for source in result.get("sources", []):
    print(source)