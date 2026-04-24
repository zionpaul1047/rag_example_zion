function PlaceholderCard({ title, desc }) {
  return (
    <div className="card">
      <h2 className="card__title">{title}</h2>
      <p className="card__desc">{desc}</p>
    </div>
  );
}

export default PlaceholderCard;