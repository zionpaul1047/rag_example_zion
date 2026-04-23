import json
import requests
import gradio as gr

API_URL = "http://127.0.0.1:8000/chat"


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return "출처 없음"

    lines = []
    for idx, src in enumerate(sources, start=1):
        source = src.get("source", "-")
        chunk_index = src.get("chunk_index", "-")
        rerank_score = src.get("rerank_score", "-")
        lines.append(
            f"{idx}. source={source}, chunk_index={chunk_index}, rerank_score={rerank_score}"
        )
    return "\n".join(lines)


def ask_normal(message: str, conversation_id_value):
    if not message.strip():
        return "", conversation_id_value, "질문을 입력해주세요."

    payload = {
        "message": message,
        "conversation_id": int(conversation_id_value) if conversation_id_value else None,
        "stream": False
    }

    response = requests.post(API_URL, json=payload, timeout=300)
    response.raise_for_status()
    data = response.json()

    answer = data.get("answer", "")
    conversation_id = data.get("conversation_id")
    sources_text = format_sources(data.get("sources", []))

    return answer, str(conversation_id), sources_text


def ask_stream(message: str, conversation_id_value):
    if not message.strip():
        yield "", conversation_id_value, "질문을 입력해주세요."
        return

    payload = {
        "message": message,
        "conversation_id": int(conversation_id_value) if conversation_id_value else None,
        "stream": True
    }

    answer_acc = ""
    final_conversation_id = conversation_id_value
    final_sources = "출처 없음"

    with requests.post(API_URL, json=payload, stream=True, timeout=300) as response:
        response.raise_for_status()

        for raw_line in response.iter_lines():
            if not raw_line:
                continue

            line = raw_line.decode("utf-8")

            if not line.startswith("data: "):
                continue

            data_str = line[6:]
            item = json.loads(data_str)

            if item.get("type") == "token":
                token = item.get("content", "")
                answer_acc += token
                final_conversation_id = str(item.get("conversation_id", final_conversation_id))
                yield answer_acc, final_conversation_id, final_sources

            elif item.get("type") == "done":
                final_conversation_id = str(item.get("conversation_id", final_conversation_id))
                final_sources = format_sources(item.get("sources", []))
                final_answer = item.get("answer", answer_acc)
                yield final_answer, final_conversation_id, final_sources


def clear_all():
    return "", "", ""


with gr.Blocks(title="AI Chatbot UI") as demo:
    gr.Markdown("# RAG 챗봇 테스트 UI")
    gr.Markdown("FastAPI `/chat` API를 호출하는 테스트용 Gradio 화면")

    with gr.Row():
        message = gr.Textbox(
            label="질문",
            placeholder="예: TV 화면이 안 나와요",
            lines=4
        )

    with gr.Row():
        conversation_id = gr.Textbox(
            label="conversation_id",
            placeholder="비워두면 새 대화 생성"
        )

    with gr.Row():
        normal_btn = gr.Button("일반 응답")
        stream_btn = gr.Button("스트리밍 응답")
        clear_btn = gr.Button("초기화")

    answer = gr.Textbox(label="답변", lines=14)
    sources = gr.Textbox(label="출처", lines=8)

    normal_btn.click(
        fn=ask_normal,
        inputs=[message, conversation_id],
        outputs=[answer, conversation_id, sources]
    )

    stream_btn.click(
        fn=ask_stream,
        inputs=[message, conversation_id],
        outputs=[answer, conversation_id, sources]
    )

    clear_btn.click(
        fn=clear_all,
        inputs=[],
        outputs=[message, conversation_id, answer]
    ).then(
        fn=lambda: "",
        inputs=[],
        outputs=sources
    )

if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)