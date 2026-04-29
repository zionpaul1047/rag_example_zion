import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

function RagDocumentsPage({ role }) {
  const canManage = role === "admin";

  const [file, setFile] = useState(null);
  const [title, setTitle] = useState("삼성 TV FAQ");
  const [category, setCategory] = useState("tv");
  const [approvedBy, setApprovedBy] = useState("admin");

  const [versionFile, setVersionFile] = useState(null);
  const [versionParentId, setVersionParentId] = useState("");

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

  const refreshAfterAction = async (messageText) => {
    setMessage(messageText);
    await loadManagedDocs();
    setSelectedDoc(null);
  };

  const uploadManagedFile = async () => {
    if (!canManage) {
      setMessage("관리자만 업로드할 수 있습니다.");
      return;
    }

    if (!file) {
      alert("파일을 선택해주세요.");
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

      setFile(null);
      await refreshAfterAction(`업로드 완료: ${data.original_name}`);
    } catch (e) {
      setMessage(`업로드 오류: ${e.message}`);
    }
  };

  const uploadManagedVersion = async () => {
    if (!canManage) {
      setMessage("관리자만 새 버전을 업로드할 수 있습니다.");
      return;
    }

    if (!versionParentId) {
      alert("기준 문서를 선택해주세요.");
      return;
    }

    if (!versionFile) {
      alert("새 버전 파일을 선택해주세요.");
      return;
    }

    const formData = new FormData();
    formData.append("file", versionFile);

    try {
      const res = await fetch(
        `${API_BASE}/admin/rag-documents/${versionParentId}/versions/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await res.json();

      if (!res.ok) {
        setMessage(`새 버전 업로드 실패: ${JSON.stringify(data)}`);
        return;
      }

      setVersionFile(null);
      setVersionParentId("");
      await refreshAfterAction(
        `새 버전 업로드 완료: ${data.title} ${data.version} (id=${data.id})`
      );
    } catch (e) {
      setMessage(`새 버전 업로드 오류: ${e.message}`);
    }
  };

  const processManaged = async (documentId) => {
    await postAction(`${API_BASE}/admin/rag-documents/${documentId}/process`, "처리");
  };

  const requestReviewManaged = async (documentId) => {
    await postAction(
      `${API_BASE}/admin/rag-documents/${documentId}/request-review`,
      "검토요청"
    );
  };

  const approveManaged = async (documentId) => {
    const formData = new FormData();
    formData.append("approved_by", approvedBy);

    await postAction(
      `${API_BASE}/admin/rag-documents/${documentId}/approve`,
      "승인",
      formData
    );
  };

  const indexManaged = async (documentId) => {
    await postAction(`${API_BASE}/admin/rag-documents/${documentId}/index`, "인덱싱");
  };

  const retireManaged = async (documentId) => {
    await postAction(`${API_BASE}/admin/rag-documents/${documentId}/retire`, "운영제외");
  };

  const rollbackReviewManaged = async (documentId) => {
    await postAction(
      `${API_BASE}/admin/rag-documents/${documentId}/rollback-review`,
      "검토취소"
    );
  };

  const rollbackApproveManaged = async (documentId) => {
    await postAction(
      `${API_BASE}/admin/rag-documents/${documentId}/rollback-approve`,
      "승인취소"
    );
  };

  const restoreManaged = async (documentId) => {
    await postAction(`${API_BASE}/admin/rag-documents/${documentId}/restore`, "복구");
  };

  const postAction = async (url, actionName, body = undefined) => {
    if (!canManage) {
      setMessage("관리자만 작업할 수 있습니다.");
      return;
    }

    try {
      const res = await fetch(url, {
        method: "POST",
        body,
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(`${actionName} 실패: ${JSON.stringify(data)}`);
        return;
      }

      await refreshAfterAction(`${actionName} 완료`);
    } catch (e) {
      setMessage(`${actionName} 오류: ${e.message}`);
    }
  };

  const deleteManaged = async (documentId) => {
    if (!canManage) {
      setMessage("관리자만 삭제할 수 있습니다.");
      return;
    }

    const confirmed = window.confirm(
      `document_id=${documentId} 문서를 삭제할까요?\n삭제 가능 상태는 draft/parsed/failed입니다.`
    );

    if (!confirmed) return;

    try {
      const res = await fetch(`${API_BASE}/admin/rag-documents/${documentId}`, {
        method: "DELETE",
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(`삭제 실패: ${JSON.stringify(data)}`);
        return;
      }

      await refreshAfterAction(`삭제 완료: document_id=${documentId}`);
    } catch (e) {
      setMessage(`삭제 오류: ${e.message}`);
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

  const normalizeStatus = (status) => String(status || "").toLowerCase();

  const renderStatusBadge = (status) => {
    const normalized = normalizeStatus(status);

    let className = "status-badge";

    if (normalized === "draft") className += " gray";
    else if (normalized === "parsed") className += " blue";
    else if (normalized === "review") className += " purple";
    else if (normalized === "approved") className += " indigo";
    else if (normalized === "indexed") className += " green";
    else if (normalized === "retired") className += " gray";
    else if (normalized === "failed") className += " red";
    else className += " gray";

    return <span className={className}>{status || "-"}</span>;
  };

  const canProcess = (status) => ["draft", "failed"].includes(normalizeStatus(status));
  const canRequestReview = (status) => normalizeStatus(status) === "parsed";
  const canApprove = (status) => normalizeStatus(status) === "review";
  const canIndex = (status) => normalizeStatus(status) === "approved";
  const canRetire = (status) => normalizeStatus(status) === "indexed";
  const canRollbackReview = (status) => normalizeStatus(status) === "review";
  const canRollbackApprove = (status) => normalizeStatus(status) === "approved";
  const canRestore = (status) => normalizeStatus(status) === "retired";
  const canDelete = (status) =>
    ["draft", "parsed", "failed"].includes(normalizeStatus(status));

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
          <button
            className="primary-btn"
            onClick={uploadManagedFile}
            disabled={!canManage}
          >
            관리 문서 업로드
          </button>

          <button className="secondary-btn" onClick={loadManagedDocs}>
            목록 새로고침
          </button>
        </div>

        <div className="inline-message">{message}</div>
      </div>

      <div className="card">
        <div className="section-header">
          <h2 className="card__title">새 버전 업로드</h2>
          <span className={canManage ? "role-pill admin" : "role-pill user"}>
            {canManage ? "버전 관리" : "읽기 전용"}
          </span>
        </div>

        <label className="field">
          <span className="field__label">기준 문서</span>
          <select
            className="field__input"
            value={versionParentId}
            onChange={(e) => setVersionParentId(e.target.value)}
            disabled={!canManage}
          >
            <option value="">기준 문서를 선택하세요</option>
            {docs.map((doc) => (
              <option key={doc.id} value={doc.id}>
                ID {doc.id} · {doc.title} · {doc.version || "v?"} · {doc.status}
                {doc.is_active ? " · ACTIVE" : ""}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span className="field__label">새 버전 파일</span>
          <input
            className="field__input"
            type="file"
            onChange={(e) => setVersionFile(e.target.files?.[0] || null)}
            disabled={!canManage}
          />
        </label>

        <div className="button-row">
          <button
            className="primary-btn"
            onClick={uploadManagedVersion}
            disabled={!canManage}
          >
            새 버전 업로드
          </button>
        </div>

        <p className="card__desc">
          새 버전은 draft 상태로 생성됩니다. 이후 처리 → 검토요청 → 승인 → 인덱싱을
          진행하면 새 버전이 ACTIVE가 되고 기존 ACTIVE 문서는 retired 처리됩니다.
        </p>
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
                      <button
                        className="link-btn"
                        onClick={() => setSelectedDoc(doc)}
                      >
                        {doc.title}
                      </button>
                    </td>

                    <td>{doc.category || "-"}</td>
                    <td>{doc.original_name}</td>
                    <td>{renderStatusBadge(doc.status)}</td>

                    <td>
                      <strong>{doc.version || "-"}</strong>
                      {doc.is_active ? <span className="active-badge">ACTIVE</span> : null}
                    </td>

                    <td>{doc.approved_by || "-"}</td>

                    <td>
                      <div className="table-actions">
                        <button
                          className="mini-btn"
                          onClick={() => setSelectedDoc(doc)}
                        >
                          보기
                        </button>

                        {canProcess(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => processManaged(doc.id)}
                            disabled={!canManage}
                          >
                            처리
                          </button>
                        )}

                        {canRequestReview(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => requestReviewManaged(doc.id)}
                            disabled={!canManage}
                          >
                            검토요청
                          </button>
                        )}

                        {canRollbackReview(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => rollbackReviewManaged(doc.id)}
                            disabled={!canManage}
                          >
                            검토취소
                          </button>
                        )}

                        {canApprove(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => approveManaged(doc.id)}
                            disabled={!canManage}
                          >
                            승인
                          </button>
                        )}

                        {canRollbackApprove(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => rollbackApproveManaged(doc.id)}
                            disabled={!canManage}
                          >
                            승인취소
                          </button>
                        )}

                        {canIndex(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => indexManaged(doc.id)}
                            disabled={!canManage}
                          >
                            인덱싱
                          </button>
                        )}

                        {canRetire(doc.status) && (
                          <button
                            className="mini-btn danger"
                            onClick={() => retireManaged(doc.id)}
                            disabled={!canManage}
                          >
                            운영제외
                          </button>
                        )}

                        {canRestore(doc.status) && (
                          <button
                            className="mini-btn"
                            onClick={() => restoreManaged(doc.id)}
                            disabled={!canManage}
                          >
                            복구
                          </button>
                        )}

                        {canDelete(doc.status) && (
                          <button
                            className="mini-btn danger"
                            onClick={() => deleteManaged(doc.id)}
                            disabled={!canManage}
                          >
                            삭제
                          </button>
                        )}

                        {normalizeStatus(doc.status) === "retired" && (
                          <span className="muted-text">운영 제외됨</span>
                        )}
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
          <p className="card__desc">
            목록에서 제목을 누르면 상세 정보를 볼 수 있습니다.
          </p>
        ) : (
          <div className="detail-grid">
            <div className="detail-meta">
              <div>
                <strong>제목:</strong> {selectedDoc.title}
              </div>
              <div>
                <strong>카테고리:</strong> {selectedDoc.category || "-"}
              </div>
              <div>
                <strong>파일명:</strong> {selectedDoc.original_name}
              </div>
              <div>
                <strong>저장경로:</strong> {selectedDoc.storage_path}
              </div>
              <div>
                <strong>유형:</strong> {selectedDoc.file_category || "-"}
              </div>
              <div>
                <strong>상태:</strong> {selectedDoc.status || "-"}
              </div>
              <div>
                <strong>버전:</strong> {selectedDoc.version || "-"}
              </div>
              <div>
                <strong>문서키:</strong> {selectedDoc.document_key || "-"}
              </div>
              <div>
                <strong>활성여부:</strong>{" "}
                {selectedDoc.is_active ? "ACTIVE" : "inactive"}
              </div>
              <div>
                <strong>상위문서ID:</strong>{" "}
                {selectedDoc.parent_document_id || "-"}
              </div>
              <div>
                <strong>승인자:</strong> {selectedDoc.approved_by || "-"}
              </div>
              <div>
                <strong>승인일:</strong> {formatDate(selectedDoc.approved_at)}
              </div>
              <div>
                <strong>생성일:</strong> {formatDate(selectedDoc.created_at)}
              </div>
              <div>
                <strong>수정일:</strong> {formatDate(selectedDoc.updated_at)}
              </div>
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