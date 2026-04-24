import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

const API_BASE = "http://127.0.0.1:8000";

function MyConversationsPage({ onOpenConversation }) {
  const { token } = useAuth();

  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [statusMessage, setStatusMessage] = useState("");

  const loadConversations = async () => {
    try {
      const res = await fetch(`${API_BASE}/conversations`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (!res.ok) {
        setStatusMessage(`대화 목록 조회 실패: ${JSON.stringify(data)}`);
        return;
      }

      setConversations(Array.isArray(data) ? data : []);
      setStatusMessage("대화 목록을 불러왔습니다.");
    } catch (e) {
      setStatusMessage(`대화 목록 조회 오류: ${e.message}`);
    }
  };

  const loadMessages = async (conversation) => {
    setSelectedConversation(conversation);

    try {
      const res = await fetch(`${API_BASE}/conversations/${conversation.id}/messages`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (!res.ok) {
        setStatusMessage(`메시지 조회 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessages(Array.isArray(data) ? data : []);
      setStatusMessage(`conversation_id=${conversation.id} 메시지를 불러왔습니다.`);
    } catch (e) {
      setStatusMessage(`메시지 조회 오류: ${e.message}`);
    }
  };

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadInitial() {
      try {
        const res = await fetch(`${API_BASE}/conversations`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!ignore) {
          setConversations(Array.isArray(data) ? data : []);
          setStatusMessage("대화 목록을 불러왔습니다.");
        }
      } catch (e) {
        if (!ignore) {
          setStatusMessage(`대화 목록 조회 오류: ${e.message}`);
        }
      }
    }

    loadInitial();

    return () => {
      ignore = true;
    };
  }, [token]);

  const formatDate = (value) => {
    if (!value) return "-";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  };

  return (
    <div className="page-grid conversation-layout">
      <div className="card">
        <div className="section-header">
          <h2 className="card__title">내 대화 목록</h2>
          <span className="muted-text">총 {conversations.length}건</span>
        </div>

        <div className="button-row">
          <button className="secondary-btn" onClick={loadConversations}>
            새로고침
          </button>
        </div>

        <div className="inline-message">{statusMessage}</div>

        <div className="conversation-list">
          {conversations.length === 0 ? (
            <div className="empty-box">대화가 없습니다.</div>
          ) : (
            conversations.map((item) => (
              <button
                key={item.id}
                className={
                  selectedConversation?.id === item.id
                    ? "conversation-item active"
                    : "conversation-item"
                }
                onClick={() => loadMessages(item)}
              >
                <div className="conversation-item__title">{item.title}</div>
                <div className="conversation-item__meta">
                  ID {item.id} · 메시지 {item.message_count}개
                </div>
                <div className="conversation-item__date">
                  {formatDate(item.updated_at)}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="card">
        <div className="section-header">
          <h2 className="card__title">대화 상세</h2>
          <span className="muted-text">
            {selectedConversation
              ? `conversation_id=${selectedConversation.id}`
              : "선택 없음"}
          </span>
        </div>

        {!selectedConversation ? (
          <p className="card__desc">왼쪽에서 대화를 선택하세요.</p>
        ) : (
          <>
            <div className="button-row">
              <button
                className="primary-btn"
                onClick={() => onOpenConversation(selectedConversation.id)}
              >
                이 대화 이어서 하기
              </button>
            </div>

            <div className="message-preview-list">
              {messages.length === 0 ? (
                <div className="empty-box">메시지가 없습니다.</div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={
                      msg.role === "user"
                        ? "message-preview user"
                        : "message-preview assistant"
                    }
                  >
                    <div className="message-preview__role">
                      {msg.role === "user" ? "사용자" : "AI"}
                    </div>
                    <div className="message-preview__content">{msg.content}</div>
                    <div className="message-preview__date">
                      {formatDate(msg.created_at)}
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default MyConversationsPage;