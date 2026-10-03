import type { Cloudinary } from '@cloudinary/url-gen';
import { ClothingImage } from '../cloudinary/images';
import type { WardrobeStats as Stats } from '../types';

interface WardrobeStatsProps {
  stats: Stats | null;
  cld: Cloudinary | null;
  onSelect: (itemId: number) => void;
}

export function WardrobeStats({ stats, cld, onSelect }: WardrobeStatsProps) {
  const total = stats?.total_items ?? 0;
  const categories = stats?.category_count ?? 0;
  const top = stats?.top_category;

  return (
    <section className="summary" aria-label="Wardrobe summary">
      <div className="summary-metrics">
        <article>
          <p className="metric">{total}</p>
          <p>{total === 1 ? 'Piece' : 'Pieces'}</p>
        </article>
        <article>
          <p className="metric">{categories}</p>
          <p>{categories === 1 ? 'Category' : 'Categories'}</p>
        </article>
        <article>
          <p className="metric metric-text">{top ?? '—'}</p>
          <p>{top ? `Most stocked · ${stats?.top_category_count ?? 0}` : 'Most stocked'}</p>
        </article>
      </div>
      <div className="recent">
        <h2>Recently added</h2>
        {stats && stats.recent_items.length > 0 ? (
          <ul>
            {stats.recent_items.map((item) => (
              <li key={item.id}>
                <button type="button" onClick={() => onSelect(item.id)}>
                  <ClothingImage
                    cld={cld}
                    publicId={item.cloudinary_public_id}
                    secureUrl={item.secure_url}
                    alt=""
                    width={120}
                    height={160}
                  />
                  <span>
                    <strong>{item.name}</strong>
                    <em>
                      {item.category} · {item.colour}
                    </em>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">New pieces will appear here.</p>
        )}
      </div>
    </section>
  );
}
