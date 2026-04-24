function Topbar({ role }) {
  return (
    <header className="topbar">
      <div>
        <h1 className="topbar__title">
          {role === "admin" ? "관리자 화면" : "사용자 화면"}
        </h1>
        <p className="topbar__desc">
          {role === "admin"
            ? "RAG 문서 관리와 운영 기능을 테스트합니다."
            : "채팅과 세션 파일 업로드를 테스트합니다."}
        </p>
      </div>
      <div className="topbar__badge">
        현재 역할: <strong>{role === "admin" ? "관리자" : "사용자"}</strong>
      </div>
    </header>
  );
}

export default Topbar;