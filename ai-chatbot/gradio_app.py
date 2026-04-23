import json
import os
import requests
import gradio as gr

API_URL = "http://127.0.0.1:8000/chat"
BASE_URL = "http://127.0.0.1:8000"


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return "출처 없음"

    lines = []
    for idx, src in enumerate(sources, start=1):
        source = src.get("source", "-")
        chunk_index = src.get("chunk_index", "-")
        rerank_score = src.get("rerank_score", "-")
        search_type = src.get("search_type", "-")
        lines.append(
            f"{idx}. source={source}, chunk_index={chunk_index}, search_type={search_type}, rerank_score={rerank_score}"
        )
    return "\n".join(lines)


def ask_normal(message: str, conversation_id_value):
    if not message.strip():
        return "", conversation_id_value, "질문을 입력해주세요."

    payload = {
        "message": message,
        "conversation_id": int(conversation_id_value) if str(conversation_id_value).strip() else None,
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
        "conversation_id": int(conversation_id_value) if str(conversation_id_value).strip() else None,
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


def clear_chat():
    return "", "", "", ""


def _safe_json(response: requests.Response):
    try:
        return response.json()
    except Exception:
        return {"raw_text": response.text}


def _basename(file_obj) -> str:
    if file_obj is None:
        return ""

    name = getattr(file_obj, "name", None)
    if not name:
        return ""
    return os.path.basename(name)


def upload_session_file(file_obj, conversation_id_value, user_id_value):
    if file_obj is None:
        return "파일을 선택해주세요.", ""

    with open(file_obj.name, "rb") as f:
        files = {
            "file": (_basename(file_obj), f, "application/octet-stream")
        }
        data = {
            "conversation_id": int(conversation_id_value) if str(conversation_id_value).strip() else None,
            "user_id": user_id_value or None
        }

        res = requests.post(
            f"{BASE_URL}/session-files/upload",
            files=files,
            data=data,
            timeout=300
        )

    data = _safe_json(res)
    if res.status_code != 200:
        return f"업로드 실패: {data}", ""

    return json.dumps(data, ensure_ascii=False, indent=2), str(data.get("conversation_id", conversation_id_value or ""))


def process_session_file(document_id_value):
    if not str(document_id_value).strip():
        return "document_id를 입력해주세요."

    res = requests.post(
        f"{BASE_URL}/session-files/{int(document_id_value)}/process",
        timeout=300
    )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


def list_session_files(conversation_id_value):
    params = {}
    if str(conversation_id_value).strip():
        params["conversation_id"] = int(conversation_id_value)

    res = requests.get(
        f"{BASE_URL}/session-files",
        params=params,
        timeout=300
    )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


def upload_managed_file(file_obj, title_value, category_value):
    if file_obj is None:
        return "파일을 선택해주세요."
    if not str(title_value).strip():
        return "title을 입력해주세요."

    with open(file_obj.name, "rb") as f:
        files = {
            "file": (_basename(file_obj), f, "application/octet-stream")
        }
        data = {
            "title": title_value,
            "category": category_value or None
        }

        res = requests.post(
            f"{BASE_URL}/admin/rag-documents/upload",
            files=files,
            data=data,
            timeout=300
        )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


def process_managed_file(document_id_value):
    if not str(document_id_value).strip():
        return "document_id를 입력해주세요."

    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{int(document_id_value)}/process",
        timeout=300
    )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


def approve_managed_file(document_id_value, approved_by_value):
    if not str(document_id_value).strip():
        return "document_id를 입력해주세요."

    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{int(document_id_value)}/approve",
        data={"approved_by": approved_by_value or None},
        timeout=300
    )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


def index_managed_file(document_id_value):
    if not str(document_id_value).strip():
        return "document_id를 입력해주세요."

    res = requests.post(
        f"{BASE_URL}/admin/rag-documents/{int(document_id_value)}/index",
        timeout=300
    )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


def list_managed_files():
    res = requests.get(
        f"{BASE_URL}/admin/rag-documents",
        timeout=300
    )

    data = _safe_json(res)
    return json.dumps(data, ensure_ascii=False, indent=2)


with gr.Blocks(title="AI Chatbot UI") as demo:
    gr.Markdown("# RAG 챗봇 테스트 UI")
    gr.Markdown("채팅 + 세션 파일 업로드 + 관리자 RAG 문서 관리")

    with gr.Tab("채팅"):
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
            fn=clear_chat,
            inputs=[],
            outputs=[message, conversation_id, answer, sources]
        )

    with gr.Tab("사용자 세션 파일 업로드"):
        gr.Markdown("현재 대화에서만 참고할 파일을 업로드합니다. 업로드 직후 자동 처리(OCR/파싱)됩니다.")

        session_file = gr.File(label="세션 파일 선택", file_count="single")
        session_user_id = gr.Textbox(label="user_id", value="zion")
        session_conversation_id = gr.Textbox(label="conversation_id", placeholder="예: 19")
        session_document_id = gr.Textbox(label="처리할 session document_id", placeholder="예: 1")

        with gr.Row():
            session_upload_btn = gr.Button("세션 파일 업로드")
            session_process_btn = gr.Button("세션 파일 재처리")
            session_list_btn = gr.Button("세션 파일 목록 조회")

        session_result = gr.Textbox(label="결과", lines=16)

        session_upload_btn.click(
            fn=upload_session_file,
            inputs=[session_file, session_conversation_id, session_user_id],
            outputs=[session_result, session_conversation_id]
        )

        session_process_btn.click(
            fn=process_session_file,
            inputs=[session_document_id],
            outputs=[session_result]
        )

        session_list_btn.click(
            fn=list_session_files,
            inputs=[session_conversation_id],
            outputs=[session_result]
        )

    with gr.Tab("관리자 RAG 문서 관리"):
        gr.Markdown("공식 KB 후보 문서를 업로드하고 처리/승인/인덱싱합니다.")

        managed_file = gr.File(label="관리 문서 선택", file_count="single")
        managed_title = gr.Textbox(label="title", placeholder="예: 삼성 TV FAQ")
        managed_category = gr.Textbox(label="category", placeholder="예: tv")
        managed_document_id = gr.Textbox(label="관리 문서 document_id", placeholder="예: 1")
        managed_approved_by = gr.Textbox(label="approved_by", value="admin")

        with gr.Row():
            managed_upload_btn = gr.Button("관리 문서 업로드")
            managed_process_btn = gr.Button("관리 문서 처리")
            managed_approve_btn = gr.Button("관리 문서 승인")
            managed_index_btn = gr.Button("관리 문서 인덱싱")
            managed_list_btn = gr.Button("관리 문서 목록 조회")

        managed_result = gr.Textbox(label="결과", lines=18)

        managed_upload_btn.click(
            fn=upload_managed_file,
            inputs=[managed_file, managed_title, managed_category],
            outputs=[managed_result]
        )

        managed_process_btn.click(
            fn=process_managed_file,
            inputs=[managed_document_id],
            outputs=[managed_result]
        )

        managed_approve_btn.click(
            fn=approve_managed_file,
            inputs=[managed_document_id, managed_approved_by],
            outputs=[managed_result]
        )

        managed_index_btn.click(
            fn=index_managed_file,
            inputs=[managed_document_id],
            outputs=[managed_result]
        )

        managed_list_btn.click(
            fn=list_managed_files,
            inputs=[],
            outputs=[managed_result]
        )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860)