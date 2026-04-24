import { useRef, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function ChatPage({ activeConversationId, onConversationChange }) {
  const [message, setMessage] = useState("");
  const [manualConversationId, setManualConversationId] = useState("");
  const [llmProvider, setLlmProvider] = useState("auto");

  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [providerInfo, setProviderInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSources, setShowSources] = useState(true);

  const abortRef = useRef(null);

  const conversationId = manualConversationId || activeConversationId || "";

  const updateConversationId = (value) => {
    setManualConversationId(value);
    if (onConversationChange) {
      onConversationChange(value);
    }
  };

  const addUserMessage = (content) => {
    setMessages((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        role: "user",
        content,
      },
    ]);
  };

  const addAssistantMessage = (content) => {
    const id = crypto.randomUUID();

    setMessages((prev) => [
      ...prev,
      {
        id,
        role: "assistant",
        content,
      },
    ]);

    return id;
  };

  const updateAssistantMessage = (id, content) => {
    setMessages((prev) =>
      prev.map((item) => (item.id === id ? { ...item, content } : item))
    );
  };

  const askNormal = async (overrideMessage) => {
    const question = overrideMessage || message;

    if (!question.trim()) {
      alert("질문을 입력해주세요.");
      return;
    }

    setLoading(true);
    setSources([]);
    setProviderInfo("");

    addUserMessage(question);
    const assistantId = addAssistantMessage("응답을 생성하고 있습니다...");

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: question,
          conversation_id: conversationId ? Number(conversationId) : null,
          stream: false,
          llm_provider: llmProvider,
        }),
      });

      const data = await res.json();

      updateAssistantMessage(assistantId, data.answer || "");
      updateConversationId(String(data.conversation_id || ""));
      setSources(data.sources || []);
      setProviderInfo(
        `요청 모델: ${data.requested_provider || llmProvider} / 실제 사용: ${
          data.used_provider || "-"
        }`
      );
      setMessage("");
    } catch (e) {
      updateAssistantMessage(assistantId, `오류: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const askStream = async (overrideMessage) => {
    const question = overrideMessage || message;

    if (!question.trim()) {
      alert("질문을 입력해주세요.");
      return;
    }

    setLoading(true);
    setSources([]);
    setProviderInfo("");

    addUserMessage(question);
    const assistantId = addAssistantMessage("");

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        signal: controller.signal,
        body: JSON.stringify({
          message: question,
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
            updateAssistantMessage(assistantId, finalAnswer);

            if (payload.conversation_id) {
              updateConversationId(String(payload.conversation_id));
            }

            setProviderInfo(
              `요청 모델: ${payload.requested_provider || llmProvider} / 실제 사용: ${
                payload.used_provider || "-"
              }`
            );
          }

          if (payload.type === "done") {
            updateAssistantMessage(assistantId, payload.answer || finalAnswer);
            setSources(payload.sources || []);

            if (payload.conversation_id) {
              updateConversationId(String(payload.conversation_id));
            }

            setProviderInfo(
              `요청 모델: ${payload.requested_provider || llmProvider} / 실제 사용: ${
                payload.used_provider || "-"
              }`
            );
          }
        }
      }

      setMessage("");
    } catch (e) {
      if (e.name === "AbortError") {
        updateAssistantMessage(assistantId, "응답 생성을 중단했습니다.");
      } else {
        updateAssistantMessage(assistantId, `오류: ${e.message}`);
      }
    } finally {
      setLoading(false);
      abortRef.current = null;
    }
  };

  const stopStreaming = () => {
    if (abortRef.current) {
      abortRef.current.abort();
    }
  };

  const startNewConversation = () => {
    updateConversationId("");
    setMessage("");
    setMessages([]);
    setSources([]);
    setProviderInfo("");
  };

  const copyText = async (text) => {
    await navigator.clipboard.writeText(text || "");
    alert("복사했습니다.");
  };

  const regenerateLast = () => {
    const lastUserMessage = [...messages].reverse().find((item) => item.role === "user");

    if (!lastUserMessage) {
      alert("재생성할 사용자 질문이 없습니다.");
      return;
    }

    askStream(lastUserMessage.content);
  };

  return (
    <div className="chat-layout">
      <div className="chat-main card">
        <div className="section-header">
          <h2 className="card__title">채팅</h2>
          <div className="button-row">
            <button className="secondary-btn" onClick={startNewConversation}>
              새 대화
            </button>
            <button className="secondary-btn" onClick={regenerateLast} disabled={loading}>
              재생성
            </button>
            <button className="secondary-btn" onClick={stopStreaming} disabled={!loading}>
              중단
            </button>
          </div>
        </div>

        <div className="chat-controls">
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
        </div>

        {providerInfo && <div className="inline-message">{providerInfo}</div>}

        <div className="message-list">
          {messages.length === 0 ? (
            <div className="empty-box">
              질문을 입력하면 대화가 시작됩니다.
            </div>
          ) : (
            messages.map((item) => (
              <div
                key={item.id}
                className={
                  item.role === "user"
                    ? "chat-message user"
                    : "chat-message assistant"
                }
              >
                <div className="chat-message__header">
                  <strong>{item.role === "user" ? "나" : "AI"}</strong>
                  <button
                    className="copy-btn"
                    onClick={() => copyText(item.content)}
                  >
                    복사
                  </button>
                </div>
                <div className="chat-message__content">{item.content}</div>
              </div>
            ))
          )}
        </div>

        <div className="chat-input-area">
          <textarea
            className="chat-input"
            rows={4}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="메시지를 입력하세요..."
            onKeyDown={(e) => {
              if (e.key === "Enter" && e.ctrlKey) {
                askStream();
              }
            }}
          />

          <div className="button-row">
            <button className="primary-btn" onClick={() => askStream()} disabled={loading}>
              스트리밍 전송
            </button>
            <button className="secondary-btn" onClick={() => askNormal()} disabled={loading}>
              일반 전송
            </button>
          </div>
        </div>
      </div>

      <div className="card source-card">
        <div className="section-header">
          <h2 className="card__title">출처</h2>
          <button
            className="secondary-btn"
            onClick={() => setShowSources((prev) => !prev)}
          >
            {showSources ? "접기" : "펼치기"}
          </button>
        </div>

        {showSources && (
          <div className="source-list">
            {sources.length === 0 ? (
              <div className="empty-box">출처 없음</div>
            ) : (
              sources.map((item, index) => (
                <div key={`${item.source}-${index}`} className="source-item">
                  <div className="source-item__title">
                    {index + 1}. {item.source}
                  </div>
                  <div className="source-item__meta">
                    chunk: {item.chunk_index ?? "-"} / type:{" "}
                    {item.search_type || "kb"}
                  </div>
                  <div className="source-item__score">
                    score: {item.rerank_score ?? "-"}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatPage;