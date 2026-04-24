import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function SessionFilesPage() {
  const [conversationId, setConversationId] = useState("19");
  const [userId, setUserId] = useState("zion");
  const [file, setFile] = useState(null);

  const [files, setFiles] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [message, setMessage] = useState("");

  const loadSessionFiles = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/session-files?conversation_id=${conversationId}`
      );
      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
      setMessage("세션 파일 목록을 불러왔습니다.");
    } catch (e) {
      setMessage(`목록 조회 오류: ${e.message}`);
    }
  };

  useEffect(() => {
  let ignore = false;

  async function loadInitialSessionFiles() {
    try {
      const res = await fetch(
        `${API_BASE}/session-files?conversation_id=${conversationId}`
      );
      const data = await res.json();

      if (!ignore) {
        setFiles(Array.isArray(data) ? data : []);
        setMessage("세션 파일 목록을 불러왔습니다.");
      }
    } catch (e) {
      if (!ignore) {
        setMessage(`목록 조회 오류: ${e.message}`);
      }
    }
  }

  loadInitialSessionFiles();

  return () => {
    ignore = true;
  };
}, [conversationId]);

  const uploadSessionFile = async () => {
    if (!file) {
      alert("파일을 선택해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("conversation_id", conversationId);
    formData.append("user_id", userId);

    try {
      const res = await fetch(`${API_BASE}/session-files/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage(`업로드 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage(`업로드 성공: ${data.original_name} (id=${data.id})`);
      setFile(null);
      await loadSessionFiles();
    } catch (e) {
      setMessage(`업로드 오류: ${e.message}`);
    }
  };

  const reprocessSessionFile = async (documentId) => {
    try {
      const res = await fetch(`${API_BASE}/session-files/${documentId}/process`, {
        method: "POST",
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage(`재처리 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage(`재처리 완료: document_id=${documentId}`);
      await loadSessionFiles();

      const refreshed = files.find((item) => item.id === documentId);
      if (refreshed) {
        setSelectedItem(refreshed);
      }
    } catch (e) {
      setMessage(`재처리 오류: ${e.message}`);
    }
  };

  const formatDate = (value) => {
    if (!value) return "-";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  };

  const renderStatusBadge = (status) => {
    const normalized = String(status || "").toLowerCase();

    let className = "status-badge";
    if (normalized === "uploaded") className += " gray";
    else if (normalized === "parsed") className += " blue";
    else if (normalized === "failed") className += " red";
    else className += " gray";

    return <span className={className}>{status || "-"}</span>;
  };

  return (
    <div className="page-grid session-layout">
      <div className="card">
        <h2 className="card__title">사용자 세션 파일 업로드</h2>

        <div className="form-grid">
          <label className="field">
            <span className="field__label">conversation_id</span>
            <input
              className="field__input"
              value={conversationId}
              onChange={(e) => setConversationId(e.target.value)}
            />
          </label>

          <label className="field">
            <span className="field__label">user_id</span>
            <input
              className="field__input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            />
          </label>
        </div>

        <label className="field">
          <span className="field__label">파일 선택</span>
          <input
            className="field__input"
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </label>

        <div className="button-row">
          <button className="primary-btn" onClick={uploadSessionFile}>
            세션 파일 업로드
          </button>
          <button className="secondary-btn" onClick={loadSessionFiles}>
            목록 새로고침
          </button>
        </div>

        <div className="inline-message">{message}</div>
      </div>

      <div className="card">
        <div className="section-header">
          <h2 className="card__title">세션 파일 목록</h2>
          <span className="muted-text">총 {files.length}건</span>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>파일명</th>
                <th>유형</th>
                <th>상태</th>
                <th>생성일</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {files.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-cell">
                    파일이 없습니다.
                  </td>
                </tr>
              ) : (
                files.map((item) => (
                  <tr key={item.id}>
                    <td>{item.id}</td>
                    <td>
                      <button
                        className="link-btn"
                        onClick={() => setSelectedItem(item)}
                      >
                        {item.original_name}
                      </button>
                    </td>
                    <td>{item.file_category || "-"}</td>
                    <td>{renderStatusBadge(item.doc_status)}</td>
                    <td>{formatDate(item.created_at)}</td>
                    <td>
                      <div className="table-actions">
                        <button
                          className="mini-btn"
                          onClick={() => setSelectedItem(item)}
                        >
                          보기
                        </button>
                        <button
                          className="mini-btn"
                          onClick={() => reprocessSessionFile(item.id)}
                        >
                          재처리
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card full-width">
        <div className="section-header">
          <h2 className="card__title">선택 파일 상세</h2>
          <span className="muted-text">
            {selectedItem ? `document_id=${selectedItem.id}` : "선택된 파일 없음"}
          </span>
        </div>

        {!selectedItem ? (
          <p className="card__desc">목록에서 파일명을 누르면 상세 정보를 볼 수 있습니다.</p>
        ) : (
          <div className="detail-grid">
            <div className="detail-meta">
              <div><strong>파일명:</strong> {selectedItem.original_name}</div>
              <div><strong>저장경로:</strong> {selectedItem.storage_path}</div>
              <div><strong>MIME:</strong> {selectedItem.mime_type || "-"}</div>
              <div><strong>확장자:</strong> {selectedItem.file_extension || "-"}</div>
              <div><strong>유형:</strong> {selectedItem.file_category || "-"}</div>
              <div><strong>상태:</strong> {selectedItem.doc_status || "-"}</div>
              <div><strong>만료일:</strong> {formatDate(selectedItem.expires_at)}</div>
            </div>

            <div className="detail-panels">
              <label className="field">
                <span className="field__label">OCR 텍스트</span>
                <textarea
                  className="field__textarea"
                  rows={8}
                  value={selectedItem.ocr_text || ""}
                  readOnly
                />
              </label>

              <label className="field">
                <span className="field__label">비전 요약</span>
                <textarea
                  className="field__textarea"
                  rows={6}
                  value={selectedItem.vision_summary || ""}
                  readOnly
                />
              </label>

              <label className="field">
                <span className="field__label">최종 parsed_text</span>
                <textarea
                  className="field__textarea"
                  rows={12}
                  value={selectedItem.parsed_text || ""}
                  readOnly
                />
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SessionFilesPage;