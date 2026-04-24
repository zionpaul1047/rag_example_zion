import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function ChatPage() {
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState("");
  const [loading, setLoading] = useState(false);

  const askNormal = async () => {
    if (!message.trim()) {
      alert("질문을 입력해주세요.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId ? Number(conversationId) : null,
          stream: false,
        }),
      });

      const data = await res.json();
      setAnswer(data.answer || "");
      setConversationId(String(data.conversation_id || ""));
      setSources(JSON.stringify(data.sources || [], null, 2));
    } catch (e) {
      setAnswer(`오류: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const askStream = async () => {
    if (!message.trim()) {
      alert("질문을 입력해주세요.");
      return;
    }

    setLoading(true);
    setAnswer("");
    setSources("");

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          conversation_id: conversationId ? Number(conversationId) : null,
          stream: true,
        }),
      });

      if (!res.body) {
        throw new Error("스트리밍 응답이 없습니다.");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let finalAnswer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";

        for (const chunk of chunks) {
          const line = chunk.split("\n").find((item) => item.startsWith("data: "));
          if (!line) continue;

          const payload = JSON.parse(line.replace("data: ", ""));

          if (payload.type === "token") {
            finalAnswer += payload.content || "";
            setAnswer(finalAnswer);
            if (payload.conversation_id) {
              setConversationId(String(payload.conversation_id));
            }
          }

          if (payload.type === "done") {
            setAnswer(payload.answer || finalAnswer);
            setSources(JSON.stringify(payload.sources || [], null, 2));
            if (payload.conversation_id) {
              setConversationId(String(payload.conversation_id));
            }
          }
        }
      }
    } catch (e) {
      setAnswer(`오류: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page-grid two-col">
      <div className="card">
        <h2 className="card__title">채팅</h2>

        <label className="field">
          <span className="field__label">conversation_id</span>
          <input
            className="field__input"
            value={conversationId}
            onChange={(e) => setConversationId(e.target.value)}
            placeholder="비워두면 새 대화 생성"
          />
        </label>

        <label className="field">
          <span className="field__label">질문</span>
          <textarea
            className="field__textarea"
            rows={6}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="예: TV 화면이 안 나와요"
          />
        </label>

        <div className="button-row">
          <button className="primary-btn" onClick={askNormal} disabled={loading}>
            일반 응답
          </button>
          <button className="secondary-btn" onClick={askStream} disabled={loading}>
            스트리밍 응답
          </button>
        </div>

        <label className="field">
          <span className="field__label">답변</span>
          <textarea className="field__textarea" rows={12} value={answer} readOnly />
        </label>
      </div>

      <div className="card">
        <h2 className="card__title">출처 / 참고 정보</h2>
        <label className="field">
          <span className="field__label">출처 목록</span>
          <textarea className="field__textarea" rows={22} value={sources} readOnly />
        </label>
      </div>
    </div>
  );
}

export default ChatPage;