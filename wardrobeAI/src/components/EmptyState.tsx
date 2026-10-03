interface EmptyStateProps {
  filtered: boolean;
  userName?: string;
  onUpload: () => void;
  onClear: () => void;
}

export function EmptyState({ filtered, userName, onUpload, onClear }: EmptyStateProps) {
  if (filtered) {
    return (
      <section className="state-panel empty-state">
        <p className="eyebrow">No matches</p>
        <h2>Nothing in the closet fits those filters.</h2>
        <p>Try another colour, category, or search, or clear the filters to see everything.</p>
        <button type="button" className="button secondary" onClick={onClear}>
          Clear filters
        </button>
      </section>
    );
  }

  return (
    <section className="state-panel empty-state">
      <p className="eyebrow">Your closet</p>
      <h2>{userName ? `Welcome to WardrobeAI, ${userName}!` : 'The wardrobe is waiting for its first piece.'}</h2>
      <p>Your digital wardrobe starts here. Upload your first clothing item and let WardrobeAI help you discover new outfit combinations.</p>
      <button type="button" className="button" onClick={onUpload}>
        Upload Your First Item
      </button>
    </section>
  );
}
