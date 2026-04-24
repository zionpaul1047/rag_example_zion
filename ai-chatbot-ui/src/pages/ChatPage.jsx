import { useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function ChatPage({ activeConversationId, onConversationChange }) {
  const [message, setMessage] = useState("");
  const [manualConversationId, setManualConversationId] = useState("");
  const [llmProvider, setLlmProvider] = useState("auto");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState("");
  const [providerInfo, setProviderInfo] = useState("");
  const [loading, setLoading] = useState(false);

  const conversationId = manualConversationId || activeConversationId || "";

  const updateConversationId = (value) => {
    setManualConversationId(value);
    if (onConversationChange) {
      onConversationChange(value);
    }
  };

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
          llm_provider: llmProvider,
        }),
      });

      const data = await res.json();

      setAnswer(data.answer || "");
      updateConversationId(String(data.conversation_id || ""));
      setSources(JSON.stringify(data.sources || [], null, 2));
      setProviderInfo(
        `요청 모델: ${data.requested_provider || llmProvider} / 실제 사용: ${data.used_provider || "-"}`
      );
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
    setProviderInfo("");

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
          llm_provider: llmProvider,
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
          const line = chunk
            .split("\n")
            .find((item) => item.startsWith("data: "));
          if (!line) continue;

          const payload = JSON.parse(line.replace("data: ", ""));

          if (payload.type === "token") {
            finalAnswer += payload.content || "";
            setAnswer(finalAnswer);

            if (payload.conversation_id) {
              updateConversationId(String(payload.conversation_id));
            }

            setProviderInfo(
              `요청 모델: ${payload.requested_provider || llmProvider} / 실제 사용: ${payload.used_provider || "-"}`
            );
          }

          if (payload.type === "done") {
            setAnswer(payload.answer || finalAnswer);
            setSources(JSON.stringify(payload.sources || [], null, 2));

            if (payload.conversation_id) {
              updateConversationId(String(payload.conversation_id));
            }

            setProviderInfo(
              `요청 모델: ${payload.requested_provider || llmProvider} / 실제 사용: ${payload.used_provider || "-"}`
            );
          }
        }
      }
    } catch (e) {
      setAnswer(`오류: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startNewConversation = () => {
    updateConversationId("");
    setMessage("");
    setAnswer("");
    setSources("");
    setProviderInfo("");
  };

  return (
    <div className="page-grid two-col">
      <div className="card">
        <div className="section-header">
          <h2 className="card__title">채팅</h2>
          <button className="secondary-btn" onClick={startNewConversation}>
            새 대화
          </button>
        </div>

        <label className="field">
          <span className="field__label">모델 선택</span>
          <select
            className="field__input"
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value)}
          >
            <option value="auto">Auto</option>
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
        </label>

        <label className="field">
          <span className="field__label">conversation_id</span>
          <input
            className="field__input"
            value={conversationId}
            onChange={(e) => updateConversationId(e.target.value)}
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

        {providerInfo && <div className="inline-message">{providerInfo}</div>}

        <label className="field">
          <span className="field__label">답변</span>
          <textarea
            className="field__textarea"
            rows={12}
            value={answer}
            readOnly
          />
        </label>
      </div>

      <div className="card">
        <h2 className="card__title">출처 / 참고 정보</h2>
        <label className="field">
          <span className="field__label">출처 목록</span>
          <textarea
            className="field__textarea"
            rows={22}
            value={sources}
            readOnly
          />
        </label>
      </div>
    </div>
  );
}

export default ChatPage;