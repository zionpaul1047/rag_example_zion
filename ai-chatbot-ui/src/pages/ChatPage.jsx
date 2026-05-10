import { useEffect, useRef, useState } from "react";
import { useAuth } from "../hooks/useAuth";

const API_BASE = "http://127.0.0.1:8000";

function ChatPage({ activeConversationId, onConversationChange }) {
  const { token } = useAuth();

  const [message, setMessage] = useState("");
  const [manualConversationId, setManualConversationId] = useState("");
  const [llmProvider, setLlmProvider] = useState("auto");

  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [retrievalDebug, setRetrievalDebug] = useState(null);
  const [providerInfo, setProviderInfo] = useState("");
  const [loading, setLoading] = useState(false);
  const [showSources, setShowSources] = useState(true);

  const abortRef = useRef(null);
  const loadedConversationRef = useRef("");

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
        sources: [],
      },
    ]);

    return id;
  };

  const updateAssistantMessage = (id, content, updates = {}) => {
    setMessages((prev) =>
      prev.map((item) => (item.id === id ? { ...item, content, ...updates } : item))
    );
  };

  const showMessageSources = (messageSources, messageRetrievalDebug = null) => {
    setSources(messageSources || []);
    setRetrievalDebug(messageRetrievalDebug);
    setShowSources(true);
  };

  const formatDebugValue = (value) => {
    if (value === null || value === undefined) return "-";
    return String(value);
  };

  const buildAssistantMetadata = (payload) => ({
    ...(payload.metadata || {}),
    sources: payload.sources || payload.metadata?.sources || [],
    used_provider: payload.used_provider,
    requested_provider: payload.requested_provider || llmProvider,
    eval_result: payload.eval_result,
    retry_count: payload.retry_count ?? 0,
    graph: payload.graph || payload.metadata?.graph,
    graph_trace: payload.graph_trace || payload.metadata?.graph_trace || [],
    error: payload.error,
    error_node: payload.error_node,
  });

  useEffect(() => {
    if (!token || !conversationId || loading) return;
    if (!/^\d+$/.test(String(conversationId))) return;
    if (loadedConversationRef.current === String(conversationId)) return;

    let ignore = false;

    async function loadConversationMessages() {
      try {
        const res = await fetch(`${API_BASE}/conversations/${conversationId}/messages`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!res.ok) {
          if (!ignore) {
            setProviderInfo(`이전 대화 조회 실패: ${JSON.stringify(data)}`);
          }
          return;
        }

        if (ignore) return;

        const restoredMessages = (Array.isArray(data) ? data : []).map((item) => ({
          id: `history-${item.id}`,
          role: item.role,
          content: item.content,
          createdAt: item.created_at,
          sources: item.sources || item.metadata?.sources || [],
          metadata: item.metadata || {},
        }));
        const lastAssistantWithDebug = [...restoredMessages]
          .reverse()
          .find(
            (item) =>
              item.role === "assistant" &&
              (item.sources?.length > 0 || item.metadata?.retrieval_debug)
          );

        setMessages(restoredMessages);
        setSources(lastAssistantWithDebug?.sources || []);
        setRetrievalDebug(lastAssistantWithDebug?.metadata?.retrieval_debug || null);
        setProviderInfo(`conversation_id=${conversationId} 이전 대화를 불러왔습니다.`);
        loadedConversationRef.current = String(conversationId);
      } catch (e) {
        if (!ignore) {
          setProviderInfo(`이전 대화 조회 오류: ${e.message}`);
        }
      }
    }

    loadConversationMessages();

    return () => {
      ignore = true;
    };
  }, [conversationId, loading, token]);

  const askNormal = async (overrideMessage) => {
    const question = overrideMessage || message;

    if (!question.trim()) {
      alert("질문을 입력해주세요.");
      return;
    }

    setLoading(true);
    setSources([]);
    setRetrievalDebug(null);
    setProviderInfo("");

    addUserMessage(question);
    const assistantId = addAssistantMessage("응답을 생성하고 있습니다...");

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: question,
          conversation_id: conversationId ? Number(conversationId) : null,
          stream: false,
          llm_provider: llmProvider,
        }),
      });

      const data = await res.json();

      updateAssistantMessage(assistantId, data.answer || "", {
        sources: data.sources || [],
        metadata: buildAssistantMetadata(data),
      });
      updateConversationId(String(data.conversation_id || ""));
      setSources(data.sources || []);
      setRetrievalDebug(data.metadata?.retrieval_debug || null);
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
    setRetrievalDebug(null);
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
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
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
            updateAssistantMessage(assistantId, payload.answer || finalAnswer, {
              sources: payload.sources || [],
              metadata: buildAssistantMetadata(payload),
            });
            setSources(payload.sources || []);
            setRetrievalDebug(payload.metadata?.retrieval_debug || null);

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
    loadedConversationRef.current = "";
    setMessage("");
    setMessages([]);
    setSources([]);
    setRetrievalDebug(null);
    setProviderInfo("");
  };

  const deleteCurrentConversation = async () => {
    if (!conversationId) {
      alert("삭제할 conversation_id가 없습니다.");
      return;
    }

    if (!window.confirm(`conversation_id=${conversationId} 대화를 삭제할까요?`)) {
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/conversations/${conversationId}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (!res.ok) {
        alert(`대화 삭제 실패: ${JSON.stringify(data)}`);
        return;
      }

      startNewConversation();
      setProviderInfo(`conversation_id=${data.conversation_id} 대화를 삭제했습니다.`);
    } catch (e) {
      alert(`대화 삭제 오류: ${e.message}`);
    }
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
            <button
              className="secondary-btn danger-btn"
              onClick={deleteCurrentConversation}
              disabled={loading || !conversationId}
            >
              대화 삭제
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
            messages.map((item) => {
              const messageSources = item.sources || [];
              const messageDebug = item.metadata?.retrieval_debug || null;
              const messageMetadata = item.metadata || {};
              const hasResponseMetadata =
                item.role === "assistant" &&
                (
                  messageMetadata.used_provider ||
                  messageMetadata.eval_result ||
                  messageMetadata.retry_count > 0 ||
                  messageMetadata.retry_query ||
                  messageMetadata.graph_trace?.length > 0 ||
                  messageMetadata.error
                );

              return (
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
                    <div className="chat-message__actions">
                      {item.role === "assistant" && messageSources.length > 0 && (
                        <button
                          className="copy-btn"
                          onClick={() =>
                            showMessageSources(
                              messageSources,
                              messageDebug
                            )
                          }
                        >
                          참조
                        </button>
                      )}
                      {item.role === "assistant" && messageSources.length === 0 && messageDebug && (
                        <button
                          className="copy-btn"
                          onClick={() => showMessageSources([], messageDebug)}
                        >
                          진단
                        </button>
                      )}
                      <button
                        className="copy-btn"
                        onClick={() => copyText(item.content)}
                      >
                        복사
                      </button>
                    </div>
                  </div>

                  <div className="chat-message__content">{item.content}</div>

                  {hasResponseMetadata && (
                    <details className="message-metadata">
                      <summary>응답 정보</summary>
                      <div className="message-metadata__grid">
                        <span>요청 모델</span>
                        <strong>
                          {formatDebugValue(messageMetadata.requested_provider)}
                        </strong>
                        <span>실제 사용</span>
                        <strong>{formatDebugValue(messageMetadata.used_provider)}</strong>
                        <span>검색 평가</span>
                        <strong>{formatDebugValue(messageMetadata.eval_result)}</strong>
                        <span>재검색</span>
                        <strong>{formatDebugValue(messageMetadata.retry_count)}</strong>
                        {messageMetadata.error && (
                          <>
                            <span>오류</span>
                            <strong>{messageMetadata.error_node || "unknown"}</strong>
                          </>
                        )}
                      </div>
                      {messageMetadata.retry_query && (
                        <div className="message-metadata__note">
                          <span>재검색 쿼리</span>
                          <code>{messageMetadata.retry_query}</code>
                        </div>
                      )}
                      {messageMetadata.graph_trace?.length > 0 && (
                        <div className="message-metadata__trace">
                          {messageMetadata.graph_trace.map((node) => (
                            <span key={`${item.id}-${node}`}>{node}</span>
                          ))}
                        </div>
                      )}
                    </details>
                  )}

                  {item.role === "assistant" && messageSources.length > 0 && (
                    <details className="message-sources">
                      <summary>참조 문서 {messageSources.length}개</summary>
                      <div className="message-source-list">
                        {messageSources.map((source, index) => (
                          <button
                            key={`${item.id}-${source.source}-${source.chunk_index ?? index}`}
                            className="message-source-chip"
                            onClick={() =>
                              showMessageSources(
                                messageSources,
                                messageDebug
                              )
                            }
                          >
                            <span>{index + 1}. {source.source}</span>
                            <small>
                              chunk {source.chunk_index ?? "-"} / {source.search_type || "kb"}
                            </small>
                          </button>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              );
            })
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
          <h2 className="card__title">참조</h2>
          <button
            className="secondary-btn"
            onClick={() => setShowSources((prev) => !prev)}
          >
            {showSources ? "접기" : "펼치기"}
          </button>
        </div>

        {showSources && (
          <>
            <div className="source-list">
              {sources.length === 0 ? (
                <div className="empty-box">참조 없음</div>
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
                  {item.content_preview && (
                    <div className="source-item__preview">
                      {item.content_preview}
                    </div>
                  )}
                </div>
              ))
            )}
            </div>

            {retrievalDebug && (
              <details className="retrieval-debug">
                <summary>검색 진단</summary>
                <div className="retrieval-debug__grid">
                  <span>이전 대화</span>
                  <strong>{formatDebugValue(retrievalDebug.history_message_count)}</strong>
                  <span>세션 문서</span>
                  <strong>{formatDebugValue(retrievalDebug.session_document_count)}</strong>
                  <span>KB 검색</span>
                  <strong>{formatDebugValue(retrievalDebug.kb_result_count)}</strong>
                  <span>후보 합계</span>
                  <strong>{formatDebugValue(retrievalDebug.merged_candidate_count)}</strong>
                  <span>rerank 결과</span>
                  <strong>{formatDebugValue(retrievalDebug.reranked_count)}</strong>
                  <span>최종 참조</span>
                  <strong>{formatDebugValue(retrievalDebug.source_count)}</strong>
                  <span>비활성 제외</span>
                  <strong>
                    {formatDebugValue(retrievalDebug.inactive_managed_filtered_count)}
                  </strong>
                </div>
              </details>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default ChatPage;
