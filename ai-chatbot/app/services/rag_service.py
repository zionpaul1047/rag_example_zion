from langchain_openai import ChatOpenAI
from app.core.settings import settings
from app.services.hybrid_retrieval_service import hybrid_search


def ask_rag(user_message: str) -> dict:
    results = hybrid_search(user_message, limit=3)

    context_texts = []
    sources = []

    for result in results:
        context_texts.append(
            f"[출처: {result['source']} / chunk {result['chunk_index']}]\n{result['content']}"
        )
        sources.append({
            "source": result["source"],
            "chunk_index": result["chunk_index"]
        })

    context = "\n\n".join(context_texts)

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
        temperature=0,
        api_key=settings.OPENAI_API_KEY
    )

    system_prompt = """
당신은 대기업 고객센터용 AI 상담사입니다.

반드시 아래 규칙을 지키세요.
1. 제공된 참고 문서 내용을 바탕으로만 답변하세요.
2. 문서에 없는 내용은 추측하지 말고 모른다고 답하세요.
3. 답변은 친절하고 간결하게 작성하세요.
4. 필요하면 주의사항도 함께 안내하세요.
5. 문서 근거가 불충분하면 '제공된 문서 기준으로는 확인되지 않습니다.' 라고 답하세요.
""".strip()

    human_prompt = f"""
사용자 질문:
{user_message}

참고 문서:
{context}

위 참고 문서를 근거로 답변해주세요.
""".strip()

    response = llm.invoke([
        ("system", system_prompt),
        ("human", human_prompt)
    ])

    return {
        "answer": response.content,
        "sources": sources
    }