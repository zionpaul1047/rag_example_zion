import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth";

const API_BASE = "http://127.0.0.1:8000";

function AdminDashboardPage() {
  const { token } = useAuth();
  const [data, setData] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => {
    let ignore = false;

    async function loadDashboard() {
      try {
        const res = await fetch(`${API_BASE}/admin/dashboard`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        const json = await res.json();

        if (!ignore) {
          if (!res.ok) {
            setMessage(`대시보드 조회 실패: ${JSON.stringify(json)}`);
            return;
          }

          setData(json);
          setMessage("");
        }
      } catch (e) {
        if (!ignore) {
          setMessage(`대시보드 조회 오류: ${e.message}`);
        }
      }
    }

    loadDashboard();

    return () => {
      ignore = true;
    };
  }, [token]);

  if (message) return <div className="card">{message}</div>;
  if (!data) return <div className="card">불러오는 중...</div>;

  return (
    <div className="page-grid">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>전체 대화</h3>
          <strong>{data.conversation_count}</strong>
        </div>

        <div className="stat-card">
          <h3>오늘 대화</h3>
          <strong>{data.today_conversation_count}</strong>
        </div>

        <div className="stat-card">
          <h3>전체 메시지</h3>
          <strong>{data.message_count}</strong>
        </div>

        <div className="stat-card">
          <h3>관리 문서</h3>
          <strong>{data.managed_doc_count}</strong>
        </div>

        <div className="stat-card green">
          <h3>ACTIVE 문서</h3>
          <strong>{data.active_doc_count}</strong>
        </div>

        <div className="stat-card gray">
          <h3>Retired 문서</h3>
          <strong>{data.retired_doc_count}</strong>
        </div>
      </div>

      <div className="card">
        <h2>최근 대화</h2>
        {data.recent_conversations.map((item) => (
          <div key={item.id} className="list-row">
            #{item.id} / {item.created_at}
          </div>
        ))}
      </div>

      <div className="card">
        <h2>최근 문서</h2>
        {data.recent_documents.map((item) => (
          <div key={item.id} className="list-row">
            #{item.id} {item.title} {item.version} [{item.status}]
          </div>
        ))}
      </div>

      <div className="card">
        <h2>문서 상태 분포</h2>
        {Object.entries(data.status_summary).map(([key, value]) => (
          <div key={key} className="list-row">
            {key}: {value}
          </div>
        ))}
      </div>
    </div>
  );
}

export default AdminDashboardPage;
