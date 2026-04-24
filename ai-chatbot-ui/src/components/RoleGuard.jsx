function RoleGuard({
  role,
  allow = [],
  title = "접근 권한 없음",
  desc = "이 화면은 현재 권한으로 접근할 수 없습니다.",
  children,
}) {
  const allowed = allow.includes(role);

  if (!allowed) {
    return (
      <div className="card">
        <h2 className="card__title">{title}</h2>
        <p className="card__desc">{desc}</p>
      </div>
    );
  }

  return children;
}

export default RoleGuard;