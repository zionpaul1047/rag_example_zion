import { useMemo, useState } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import PlaceholderCard from "./components/PlaceholderCard";
import RoleGuard from "./components/RoleGuard";
import ChatPage from "./pages/ChatPage";
import SessionFilesPage from "./pages/SessionFilesPage";
import RagDocumentsPage from "./pages/RagDocumentsPage";
import LoginPage from "./pages/LoginPage";
import { useAuth } from "./context/AuthContext";

function App() {
  const { isAuthenticated, role } = useAuth();
  const [menu, setMenu] = useState("chat");

  const visibleMenus = useMemo(() => {
    const common = [
      { key: "chat", label: "채팅" },
      { key: "session-files", label: "세션 파일" },
      { key: "settings", label: "설정" },
    ];

    if (role === "admin") {
      return [
        { key: "dashboard", label: "대시보드" },
        ...common,
        { key: "rag-docs", label: "RAG 문서 관리" },
        { key: "index-jobs", label: "인덱싱 작업" },
        { key: "quality-test", label: "품질 테스트" },
      ];
    }

    return [
      { key: "chat", label: "채팅" },
      { key: "my-conversations", label: "내 대화" },
      { key: "session-files", label: "세션 파일" },
      { key: "settings", label: "설정" },
    ];
  }, [role]);

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const renderPage = () => {
    switch (menu) {
      case "chat":
        return <ChatPage role={role} />;

      case "session-files":
        return <SessionFilesPage role={role} />;

      case "rag-docs":
        return (
          <RoleGuard
            role={role}
            allow={["admin"]}
            title="관리자 전용 화면"
            desc="RAG 문서 관리는 관리자만 접근할 수 있습니다."
          >
            <RagDocumentsPage role={role} />
          </RoleGuard>
        );

      case "dashboard":
        return (
          <RoleGuard
            role={role}
            allow={["admin"]}
            title="관리자 전용 화면"
            desc="대시보드는 관리자만 볼 수 있습니다."
          >
            <PlaceholderCard title="대시보드" desc="관리자 운영 요약 영역입니다." />
          </RoleGuard>
        );

      case "my-conversations":
        return (
          <PlaceholderCard
            title="내 대화"
            desc="이전 conversation 목록을 여기에 연결할 예정입니다."
          />
        );

      case "index-jobs":
        return (
          <RoleGuard
            role={role}
            allow={["admin"]}
            title="관리자 전용 화면"
            desc="인덱싱 작업 화면은 관리자만 접근할 수 있습니다."
          >
            <PlaceholderCard
              title="인덱싱 작업"
              desc="인덱싱 상태 및 최근 작업 이력을 여기에 표시합니다."
            />
          </RoleGuard>
        );

      case "quality-test":
        return (
          <RoleGuard
            role={role}
            allow={["admin"]}
            title="관리자 전용 화면"
            desc="품질 테스트 화면은 관리자만 접근할 수 있습니다."
          >
            <PlaceholderCard
              title="품질 테스트"
              desc="검색 결과 / reranker / provider 테스트 화면을 여기에 추가합니다."
            />
          </RoleGuard>
        );

      case "settings":
        return (
          <PlaceholderCard
            title="설정"
            desc="모델, 스트리밍, 표시 옵션을 여기에 구성할 예정입니다."
          />
        );

      default:
        return <PlaceholderCard title="준비 중" desc="페이지를 준비 중입니다." />;
    }
  };

  return (
    <div className="app-shell">
      <Sidebar menu={menu} visibleMenus={visibleMenus} onMenuChange={setMenu} />

      <main className="main-panel">
        <Topbar role={role} />
        <section className="page-content">{renderPage()}</section>
      </main>
    </div>
  );
}

export default App;