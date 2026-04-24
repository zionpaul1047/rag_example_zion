import { useAuth } from "../context/AuthContext";

function Sidebar({ menu, visibleMenus, onMenuChange }) {
  const { user, logout } = useAuth();

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <div className="sidebar__logo">R</div>
        <div>
          <div className="sidebar__title">RAG 챗봇</div>
          <div className="sidebar__subtitle">AI Chatbot UI</div>
        </div>
      </div>

      <div className="sidebar__section">
        <div className="sidebar__section-title">로그인 사용자</div>
        <div className="user-panel">
          <div className="user-panel__name">{user?.display_name || user?.username}</div>
          <div className="user-panel__role">{user?.role === "admin" ? "관리자" : "사용자"}</div>
        </div>
        <button className="logout-btn" onClick={logout}>
          로그아웃
        </button>
      </div>

      <div className="sidebar__section">
        <div className="sidebar__section-title">메뉴</div>
        <nav className="sidebar__menu">
          {visibleMenus.map((item) => (
            <button
              key={item.key}
              className={menu === item.key ? "menu-btn active" : "menu-btn"}
              onClick={() => onMenuChange(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </div>
    </aside>
  );
}

export default Sidebar;