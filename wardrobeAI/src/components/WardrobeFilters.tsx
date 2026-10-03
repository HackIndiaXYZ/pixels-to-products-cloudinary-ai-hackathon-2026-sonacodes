import { CATEGORIES, OCCASIONS, PATTERNS, STYLES } from '../constants';
import type { ItemQuery } from '../types';

interface WardrobeFiltersProps {
  query: ItemQuery;
  search: string;
  colours: string[];
  onSearch: (value: string) => void;
  onChange: (patch: Partial<ItemQuery>) => void;
  onClear: () => void;
}

export function WardrobeFilters({
  query,
  search,
  colours,
  onSearch,
  onChange,
  onClear,
}: WardrobeFiltersProps) {
  const colourOptions = colours.includes(query.colour) || !query.colour
    ? colours
    : [query.colour, ...colours];
  const filtersActive = Boolean(
    search.trim() || query.category || query.colour || query.pattern || query.style || query.occasion,
  );

  return (
    <section className="filters" aria-label="Search and filter the wardrobe">
      <label className="field search-field">
        <span>Search</span>
        <input
          type="search"
          value={search}
          onChange={(event) => onSearch(event.target.value)}
          placeholder="Name, colour, or brand"
        />
      </label>
      <label className="field">
        <span>Category</span>
        <select
          value={query.category}
          onChange={(event) => onChange({ category: event.target.value, page: 1 })}
        >
          <option value="">All categories</option>
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Colour</span>
        <select
          value={query.colour}
          onChange={(event) => onChange({ colour: event.target.value, page: 1 })}
        >
          <option value="">All colours</option>
          {colourOptions.map((colour) => (
            <option key={colour} value={colour}>
              {colour}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Pattern</span>
        <select
          value={query.pattern}
          onChange={(event) => onChange({ pattern: event.target.value, page: 1 })}
        >
          <option value="">All patterns</option>
          {PATTERNS.map((pattern) => (
            <option key={pattern} value={pattern}>
              {pattern}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Style</span>
        <select
          value={query.style}
          onChange={(event) => onChange({ style: event.target.value, page: 1 })}
        >
          <option value="">All styles</option>
          {STYLES.map((style) => (
            <option key={style} value={style}>
              {style}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Occasion</span>
        <select
          value={query.occasion}
          onChange={(event) => onChange({ occasion: event.target.value, page: 1 })}
        >
          <option value="">All occasions</option>
          {OCCASIONS.map((occasion) => (
            <option key={occasion} value={occasion}>
              {occasion}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Sort</span>
        <select
          value={query.sort}
          onChange={(event) =>
            onChange({ sort: event.target.value as ItemQuery['sort'], page: 1 })
          }
        >
          <option value="recent">Recently added</option>
          <option value="oldest">Oldest first</option>
          <option value="name">Alphabetical</option>
        </select>
      </label>
      {filtersActive && (
        <button type="button" className="button ghost" onClick={onClear}>
          Clear
        </button>
      )}
    </section>
  );
}
