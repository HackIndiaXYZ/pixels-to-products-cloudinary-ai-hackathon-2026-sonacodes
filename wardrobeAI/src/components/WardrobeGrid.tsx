import { useEffect } from 'react';
import type { Cloudinary } from '@cloudinary/url-gen';
import type { ClothingItem } from '../types';
import { ClothingCard } from './ClothingCard';

interface WardrobeGridProps {
  items: ClothingItem[];
  cld: Cloudinary | null;
  highlightId: number | null;
  onSelect: (itemId: number) => void;
}

export function WardrobeGrid({ items, cld, highlightId, onSelect }: WardrobeGridProps) {
  useEffect(() => {
    if (!highlightId) return;
    document.getElementById(`item-${highlightId}`)?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
  }, [highlightId, items]);

  return (
    <section className="wardrobe-grid" aria-label="Clothing items">
      {items.map((item) => (
        <ClothingCard
          key={item.id}
          item={item}
          cld={cld}
          highlighted={item.id === highlightId}
          onSelect={onSelect}
        />
      ))}
    </section>
  );
}
