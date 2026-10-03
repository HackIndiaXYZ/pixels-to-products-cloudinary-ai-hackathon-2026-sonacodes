import type { Cloudinary } from '@cloudinary/url-gen';
import { ClothingImage } from '../cloudinary/images';
import type { ClothingItem } from '../types';

interface ClothingCardProps {
  item: ClothingItem;
  cld: Cloudinary | null;
  highlighted: boolean;
  onSelect: (itemId: number) => void;
}

export function ClothingCard({ item, cld, highlighted, onSelect }: ClothingCardProps) {
  return (
    <article
      id={`item-${item.id}`}
      className={highlighted ? 'clothing-card is-highlighted' : 'clothing-card'}
    >
      <button type="button" className="card-open" onClick={() => onSelect(item.id)}>
        <div className="card-media">
          <ClothingImage
            cld={cld}
            publicId={item.cloudinary_public_id}
            secureUrl={item.secure_url}
            alt={item.name}
            width={480}
            height={640}
          />
        </div>
        <div className="card-body">
          <h3>{item.name}</h3>
          <p>
            {item.category} · {item.colour}
          </p>
          <p className="muted">
            {item.style} · {item.occasion}
          </p>
        </div>
      </button>
    </article>
  );
}
