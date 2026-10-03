import type { Cloudinary } from '@cloudinary/url-gen';
import type { ItemPage, ItemQuery, WardrobeStats as Stats } from '../types';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';
import { LoadingState } from './LoadingState';
import { WardrobeFilters } from './WardrobeFilters';
import { WardrobeGrid } from './WardrobeGrid';
import { WardrobeStats } from './WardrobeStats';

interface DashboardProps {
  id?: string;
  cld: Cloudinary | null;
  loading: boolean;
  error: string | null;
  stats: Stats | null;
  pageData: ItemPage | null;
  query: ItemQuery;
  search: string;
  highlightId: number | null;
  onRetry: () => void;
  onSearch: (value: string) => void;
  onQueryChange: (patch: Partial<ItemQuery>) => void;
  onClearFilters: () => void;
  onSelect: (itemId: number) => void;
  onUpload: () => void;
  userName?: string;
}

export function Dashboard({
  id,
  cld,
  loading,
  error,
  stats,
  pageData,
  query,
  search,
  highlightId,
  onRetry,
  onSearch,
  onQueryChange,
  onClearFilters,
  onSelect,
  onUpload,
  userName,
}: DashboardProps) {
  const filtered = Boolean(
    search.trim() || query.category || query.colour || query.pattern || query.style || query.occasion,
  );
  const items = pageData?.items ?? [];
  const showEmpty = !loading && !error && items.length === 0;

  return (
    <div className="dashboard" id={id}>
      <WardrobeStats stats={stats} cld={cld} onSelect={onSelect} />
      <div className="toolbar">
        <WardrobeFilters
          query={query}
          search={search}
          colours={stats?.colours ?? []}
          onSearch={onSearch}
          onChange={onQueryChange}
          onClear={onClearFilters}
        />
        <button type="button" className="button" onClick={onUpload}>
          Add clothing
        </button>
      </div>
      {error && <ErrorState message={error} onRetry={onRetry} />}
      {loading && !error && <LoadingState />}
      {showEmpty && <EmptyState filtered={filtered} userName={userName} onUpload={onUpload} onClear={onClearFilters} />}
      {!loading && !error && items.length > 0 && (
        <WardrobeGrid items={items} cld={cld} highlightId={highlightId} onSelect={onSelect} />
      )}
      {!loading && !error && pageData && pageData.pages > 1 && (
        <nav className="pager" aria-label="Wardrobe pages">
          <button
            type="button"
            className="button secondary"
            disabled={query.page <= 1}
            onClick={() => onQueryChange({ page: query.page - 1 })}
          >
            Previous
          </button>
          <p>
            Page {pageData.page} of {pageData.pages}
          </p>
          <button
            type="button"
            className="button secondary"
            disabled={query.page >= pageData.pages}
            onClick={() => onQueryChange({ page: query.page + 1 })}
          >
            Next
          </button>
        </nav>
      )}
    </div>
  );
}
