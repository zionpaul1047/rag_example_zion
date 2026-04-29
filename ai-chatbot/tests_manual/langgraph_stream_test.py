from app.services.rag_service import ask_rag_stream

print("=== LangGraph Stream Test ===")

events = ask_rag_stream(
    "TV 화면이 안 나와요",
    llm_provider="openai",
)

for event in events:
    print(event)

    if event.get("type") == "done":
        print("\nDONE")
        print("graph:", event.get("graph"))
        print("eval_result:", event.get("eval_result"))
        print("used_provider:", event.get("used_provider"))
        print("answer:", event.get("answer")[:300])
        print("graph_trace:", event.get("graph_trace"))