import { useState } from "react";
import { useAuth } from "../context/AuthContext";

function LoginPage() {
  const { login, loading } = useAuth();

  const [username, setUsername] = useState("zion");
  const [password, setPassword] = useState("user1234");
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await login(username, password);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-page">
      <form className="login-card" onSubmit={handleLogin}>
        <div className="login-logo">R</div>

        <h1 className="login-title">RAG 챗봇 로그인</h1>
        <p className="login-desc">계정에 따라 사용자/관리자 화면이 분리됩니다.</p>

        <label className="field">
          <span className="field__label">아이디</span>
          <input
            className="field__input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="zion 또는 admin"
          />
        </label>

        <label className="field">
          <span className="field__label">비밀번호</span>
          <input
            className="field__input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="user1234 또는 admin1234"
          />
        </label>

        {error && <div className="login-error">{error}</div>}

        <button className="primary-btn login-btn" type="submit" disabled={loading}>
          {loading ? "로그인 중..." : "로그인"}
        </button>

        <div className="login-hint">
          <div>사용자: zion / user1234</div>
          <div>관리자: admin / admin1234</div>
        </div>
      </form>
    </div>
  );
}

export default LoginPage;