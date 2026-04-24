import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

const API_BASE = "http://127.0.0.1:8000";

function AdminDashboardPage() {
  const { token } = useAuth();

  const [summary, setSummary] = useState(null);
  const [message, setMessage] = useState("");

  const loadSummary = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/dashboard/summary`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(`대시보드 조회 실패: ${JSON.stringify(data)}`);
        return;
      }

      setSummary(data);
      setMessage("대시보드 정보를 불러왔습니다.");
    } catch (e) {
      setMessage(`대시보드 조회 오류: ${e.message}`);
    }
  };

  useEffect(() => {
    if (!token) return;

    let ignore = false;

    async function loadInitialSummary() {
      try {
        const res = await fetch(`${API_BASE}/admin/dashboard/summary`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = await res.json();

        if (!ignore) {
          setSummary(data);
          setMessage("대시보드 정보를 불러왔습니다.");
        }
      } catch (e) {
        if (!ignore) {
          setMessage(`대시보드 조회 오류: ${e.message}`);
        }
      }
    }

    loadInitialSummary();

    return () => {
      ignore = true;
    };
  }, [token]);

  const recentDocs = summary?.recent_managed_documents || [];

  return (
    <div className="page-grid dashboard-layout">
      <div className="card full-width">
        <div className="section-header">
          <h2 className="card__title">관리자 대시보드</h2>
          <button className="secondary-btn" onClick={loadSummary}>
            새로고침
          </button>
        </div>
        <div className="inline-message">{message}</div>
      </div>

      <MetricCard title="전체 대화 수" value={summary?.total_conversations ?? 0} />
      <MetricCard title="전체 메시지 수" value={summary?.total_messages ?? 0} />
      <MetricCard title="세션 파일 수" value={summary?.total_session_documents ?? 0} />
      <MetricCard title="처리 완료 세션 파일" value={summary?.parsed_session_documents ?? 0} />
      <MetricCard title="관리 문서 수" value={summary?.total_managed_documents ?? 0} />
      <MetricCard title="인덱싱 완료 문서" value={summary?.indexed_managed_documents ?? 0} />
      <MetricCard title="실패 문서" value={summary?.failed_managed_documents ?? 0} />

      <div className="card full-width">
        <div className="section-header">
          <h2 className="card__title">최근 관리 문서</h2>
          <span className="muted-text">최근 {recentDocs.length}건</span>
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
                <th>수정일</th>
              </tr>
            </thead>
            <tbody>
              {recentDocs.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-cell">
                    최근 문서가 없습니다.
                  </td>
                </tr>
              ) : (
                recentDocs.map((doc) => (
                  <tr key={doc.id}>
                    <td>{doc.id}</td>
                    <td>{doc.title}</td>
                    <td>{doc.category || "-"}</td>
                    <td>{doc.original_name}</td>
                    <td>{doc.status}</td>
                    <td>{formatDate(doc.updated_at)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value }) {
  return (
    <div className="card metric-card">
      <div className="metric-card__title">{title}</div>
      <div className="metric-card__value">{value}</div>
    </div>
  );
}

function formatDate(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString();
  } catch {
    return value;
  }
}

export default AdminDashboardPage;