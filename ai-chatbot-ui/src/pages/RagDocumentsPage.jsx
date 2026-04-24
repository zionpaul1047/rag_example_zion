import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function RagDocumentsPage({ role }) {
  const canManage = role === "admin";

  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("삼성 TV FAQ");
  const [category, setCategory] = useState("tv");
  const [approvedBy, setApprovedBy] = useState("admin");

  const [docs, setDocs] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [message, setMessage] = useState("");

  const loadManagedDocs = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents`);
      const data = await res.json();
      setDocs(Array.isArray(data) ? data : []);
      setMessage("관리 문서 목록을 불러왔습니다.");
    } catch (e) {
      setMessage(`목록 조회 오류: ${e.message}`);
    }
  };

  useEffect(() => {
  let ignore = false;

  async function loadInitialManagedDocs() {
    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents`);
      const data = await res.json();

      if (!ignore) {
        setDocs(Array.isArray(data) ? data : []);
        setMessage("관리 문서 목록을 불러왔습니다.");
      }
    } catch (e) {
      if (!ignore) {
        setMessage(`목록 조회 오류: ${e.message}`);
      }
    }
  }

  loadInitialManagedDocs();

  return () => {
    ignore = true;
  };
}, []);

  const uploadManagedFile = async () => {
    if (!canManage) {
      setMessage("관리자만 문서를 업로드할 수 있습니다.");
      return;
    }

    if (!file) {
      alert("파일을 선택해주세요.");
      return;
    }
    if (!title.trim()) {
      alert("title을 입력해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("title", title);
    formData.append("category", category);

    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage(`업로드 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage(`관리 문서 업로드 성공: ${data.original_name} (id=${data.id})`);
      setFile(null);
      await loadManagedDocs();
    } catch (e) {
      setMessage(`업로드 오류: ${e.message}`);
    }
  };

  const processManaged = async (documentId) => {
    if (!canManage) {
      setMessage("관리자만 문서를 처리할 수 있습니다.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents/${documentId}/process`, {
        method: "POST",
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage(`처리 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage(`문서 처리 완료: document_id=${documentId}`);
      await loadManagedDocs();
    } catch (e) {
      setMessage(`처리 오류: ${e.message}`);
    }
  };

  const approveManaged = async (documentId) => {
    if (!canManage) {
      setMessage("관리자만 문서를 승인할 수 있습니다.");
      return;
    }

    const formData = new FormData();
    formData.append("approved_by", approvedBy);

    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents/${documentId}/approve`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage(`승인 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage(`문서 승인 완료: document_id=${documentId}`);
      await loadManagedDocs();
    } catch (e) {
      setMessage(`승인 오류: ${e.message}`);
    }
  };

  const indexManaged = async (documentId) => {
    if (!canManage) {
      setMessage("관리자만 문서를 인덱싱할 수 있습니다.");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents/${documentId}/index`, {
        method: "POST",
      });
      const data = await res.json();

      if (!res.ok) {
        setMessage(`인덱싱 실패: ${JSON.stringify(data)}`);
        return;
      }

      setMessage(`문서 인덱싱 완료: document_id=${documentId}`);
      await loadManagedDocs();
    } catch (e) {
      setMessage(`인덱싱 오류: ${e.message}`);
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
    if (normalized === "draft") className += " gray";
    else if (normalized === "parsed") className += " blue";
    else if (normalized === "approved") className += " purple";
    else if (normalized === "indexed") className += " green";
    else if (normalized === "failed") className += " red";
    else className += " gray";

    return <span className={className}>{status || "-"}</span>;
  };

  return (
    <div className="page-grid rag-layout">
      <div className="card">
        <div className="section-header">
          <h2 className="card__title">관리 문서 업로드</h2>
          <span className={canManage ? "role-pill admin" : "role-pill user"}>
            {canManage ? "관리 가능" : "읽기 전용"}
          </span>
        </div>

        <label className="field">
          <span className="field__label">문서 파일</span>
          <input
            className="field__input"
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            disabled={!canManage}
          />
        </label>

        <div className="form-grid">
          <label className="field">
            <span className="field__label">title</span>
            <input
              className="field__input"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              disabled={!canManage}
            />
          </label>

          <label className="field">
            <span className="field__label">category</span>
            <input
              className="field__input"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              disabled={!canManage}
            />
          </label>
        </div>

        <label className="field">
          <span className="field__label">approved_by</span>
          <input
            className="field__input"
            value={approvedBy}
            onChange={(e) => setApprovedBy(e.target.value)}
            disabled={!canManage}
          />
        </label>

        <div className="button-row">
          <button className="primary-btn" onClick={uploadManagedFile} disabled={!canManage}>
            관리 문서 업로드
          </button>
          <button className="secondary-btn" onClick={loadManagedDocs}>
            목록 새로고침
          </button>
        </div>

        <div className="inline-message">{message}</div>
      </div>

      <div className="card full-width">
        <div className="section-header">
          <h2 className="card__title">관리 문서 목록</h2>
          <span className="muted-text">총 {docs.length}건</span>
        </div>

        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>제목</th>
                <th>카테고리</th>
                <th>파일명</th>
                <th>상태</th>
                <th>버전</th>
                <th>승인자</th>
                <th>액션</th>
              </tr>
            </thead>
            <tbody>
              {docs.length === 0 ? (
                <tr>
                  <td colSpan="8" className="empty-cell">
                    문서가 없습니다.
                  </td>
                </tr>
              ) : (
                docs.map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.id}</td>
                    <td>
                      <button className="link-btn" onClick={() => setSelectedDoc(doc)}>
                        {doc.title}
                      </button>
                    </td>
                    <td>{doc.category || "-"}</td>
                    <td>{doc.original_name}</td>
                    <td>{renderStatusBadge(doc.status)}</td>
                    <td>{doc.version || "-"}</td>
                    <td>{doc.approved_by || "-"}</td>
                    <td>
                      <div className="table-actions">
                        <button className="mini-btn" onClick={() => setSelectedDoc(doc)}>
                          보기
                        </button>
                        <button
                          className="mini-btn"
                          onClick={() => processManaged(doc.id)}
                          disabled={!canManage}
                        >
                          처리
                        </button>
                        <button
                          className="mini-btn"
                          onClick={() => approveManaged(doc.id)}
                          disabled={!canManage}
                        >
                          승인
                        </button>
                        <button
                          className="mini-btn"
                          onClick={() => indexManaged(doc.id)}
                          disabled={!canManage}
                        >
                          인덱싱
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
          <h2 className="card__title">문서 상세</h2>
          <span className="muted-text">
            {selectedDoc ? `document_id=${selectedDoc.id}` : "선택된 문서 없음"}
          </span>
        </div>

        {!selectedDoc ? (
          <p className="card__desc">목록에서 제목을 누르면 상세 정보를 볼 수 있습니다.</p>
        ) : (
          <div className="detail-grid">
            <div className="detail-meta">
              <div><strong>제목:</strong> {selectedDoc.title}</div>
              <div><strong>카테고리:</strong> {selectedDoc.category || "-"}</div>
              <div><strong>파일명:</strong> {selectedDoc.original_name}</div>
              <div><strong>저장경로:</strong> {selectedDoc.storage_path}</div>
              <div><strong>유형:</strong> {selectedDoc.file_category || "-"}</div>
              <div><strong>상태:</strong> {selectedDoc.status || "-"}</div>
              <div><strong>버전:</strong> {selectedDoc.version || "-"}</div>
              <div><strong>승인자:</strong> {selectedDoc.approved_by || "-"}</div>
              <div><strong>승인일:</strong> {formatDate(selectedDoc.approved_at)}</div>
              <div><strong>생성일:</strong> {formatDate(selectedDoc.created_at)}</div>
              <div><strong>수정일:</strong> {formatDate(selectedDoc.updated_at)}</div>
            </div>

            <div className="detail-panels">
              <label className="field">
                <span className="field__label">parsed_text</span>
                <textarea
                  className="field__textarea"
                  rows={18}
                  value={selectedDoc.parsed_text || ""}
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

export default RagDocumentsPage;