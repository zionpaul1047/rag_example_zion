import { useState } from "react";
import axios from "axios";

function App() {
  const [message, setMessage] = useState("");
  const [chatList, setChatList] = useState([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!message.trim()) return;

    const userMessage = message;

    setChatList((prev) => [
      ...prev,
      { role: "user", text: userMessage }
    ]);

    setMessage("");
    setLoading(true);

    try {
      const response = await axios.post("http://127.0.0.1:8000/chat", {
        message: userMessage,
      });

      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          text: response.data.answer,
          sources: response.data.sources || [],
        },
      ]);
    } catch (error) {
      setChatList((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "오류가 발생했습니다. 서버 연결 상태를 확인해주세요.",
          sources: [],
        },
      ]);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      sendMessage();
    }
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>AI 고객센터 챗봇</h1>

      <div style={styles.chatBox}>
        {chatList.length === 0 && (
          <div style={styles.emptyText}>
            질문을 입력하면 AI가 답변합니다.
          </div>
        )}

        {chatList.map((item, index) => (
          <div
            key={index}
            style={
              item.role === "user" ? styles.userMessageBox : styles.aiMessageBox
            }
          >
            <div style={styles.roleLabel}>
              {item.role === "user" ? "사용자" : "AI 상담사"}
            </div>
            <div>{item.text}</div>

            {item.sources && item.sources.length > 0 && (
              <div style={styles.sourceBox}>
                <div style={styles.sourceTitle}>참고 출처</div>
                {item.sources.map((source, i) => (
                  <div key={i}>
                    - {source.source} / chunk {source.chunk_index}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && <div style={styles.loading}>답변 생성 중...</div>}
      </div>

      <div style={styles.inputArea}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="질문을 입력하세요"
          style={styles.input}
        />
        <button onClick={sendMessage} style={styles.button}>
          전송
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: {
    maxWidth: "900px",
    margin: "0 auto",
    padding: "40px 20px",
    fontFamily: "Arial, sans-serif",
  },
  title: {
    textAlign: "center",
    marginBottom: "20px",
  },
  chatBox: {
    border: "1px solid #ddd",
    borderRadius: "12px",
    padding: "20px",
    minHeight: "500px",
    backgroundColor: "#fafafa",
    marginBottom: "20px",
    overflowY: "auto",
  },
  emptyText: {
    color: "#888",
    textAlign: "center",
    marginTop: "200px",
  },
  userMessageBox: {
    backgroundColor: "#dbeafe",
    padding: "12px",
    borderRadius: "10px",
    marginBottom: "12px",
    marginLeft: "120px",
  },
  aiMessageBox: {
    backgroundColor: "#f3f4f6",
    padding: "12px",
    borderRadius: "10px",
    marginBottom: "12px",
    marginRight: "120px",
  },
  roleLabel: {
    fontWeight: "bold",
    marginBottom: "6px",
  },
  sourceBox: {
    marginTop: "10px",
    fontSize: "13px",
    color: "#555",
    borderTop: "1px solid #ddd",
    paddingTop: "8px",
  },
  sourceTitle: {
    fontWeight: "bold",
    marginBottom: "4px",
  },
  loading: {
    textAlign: "center",
    color: "#666",
    marginTop: "10px",
  },
  inputArea: {
    display: "flex",
    gap: "10px",
  },
  input: {
    flex: 1,
    padding: "12px",
    fontSize: "16px",
    borderRadius: "8px",
    border: "1px solid #ccc",
  },
  button: {
    padding: "12px 20px",
    fontSize: "16px",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "#2563eb",
    color: "white",
    cursor: "pointer",
  },
};

export default App;