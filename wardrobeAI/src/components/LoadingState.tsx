export function LoadingState() {
  return (
    <div className="state-panel" role="status" aria-live="polite">
      <div className="skeleton-grid" aria-hidden="true">
        {Array.from({ length: 6 }, (_, index) => (
          <div key={index} className="skeleton-card" />
        ))}
      </div>
      <p>Opening your wardrobe…</p>
    </div>
  );
}
