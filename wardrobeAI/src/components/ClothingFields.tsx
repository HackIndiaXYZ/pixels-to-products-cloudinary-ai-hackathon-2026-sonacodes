import { CATEGORIES, OCCASIONS, PATTERNS, SEASONS, STYLES } from '../constants';
import type { ClothingFormValues } from '../types';

interface ClothingFieldsProps {
  values: ClothingFormValues;
  errors: Record<string, string>;
  disabled?: boolean;
  onChange: (field: keyof ClothingFormValues, value: string) => void;
}

export function ClothingFields({ values, errors, disabled = false, onChange }: ClothingFieldsProps) {
  return (
    <div className="fields">
      <label className="field">
        <span>Name</span>
        <input
          value={values.name}
          onChange={(event) => onChange('name', event.target.value)}
          disabled={disabled}
          maxLength={80}
          required
          aria-invalid={Boolean(errors.name)}
        />
        {errors.name && <small role="alert">{errors.name}</small>}
      </label>

      <label className="field">
        <span>Category</span>
        <select
          value={values.category}
          onChange={(event) => onChange('category', event.target.value)}
          disabled={disabled}
          required
          aria-invalid={Boolean(errors.category)}
        >
          <option value="">Select category</option>
          {CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
        {errors.category && <small role="alert">{errors.category}</small>}
      </label>

      <label className="field">
        <span>Colour</span>
        <input
          value={values.colour}
          onChange={(event) => onChange('colour', event.target.value)}
          disabled={disabled}
          maxLength={40}
          placeholder="Ivory, navy, camel"
          required
          aria-invalid={Boolean(errors.colour)}
        />
        {errors.colour && <small role="alert">{errors.colour}</small>}
      </label>

      <label className="field">
        <span>Pattern</span>
        <select
          value={values.pattern}
          onChange={(event) => onChange('pattern', event.target.value)}
          disabled={disabled}
          required
          aria-invalid={Boolean(errors.pattern)}
        >
          <option value="">Select pattern</option>
          {PATTERNS.map((pattern) => (
            <option key={pattern} value={pattern}>
              {pattern}
            </option>
          ))}
        </select>
        {errors.pattern && <small role="alert">{errors.pattern}</small>}
      </label>

      <label className="field">
        <span>Style</span>
        <select
          value={values.style}
          onChange={(event) => onChange('style', event.target.value)}
          disabled={disabled}
          required
          aria-invalid={Boolean(errors.style)}
        >
          <option value="">Select style</option>
          {STYLES.map((style) => (
            <option key={style} value={style}>
              {style}
            </option>
          ))}
        </select>
        {errors.style && <small role="alert">{errors.style}</small>}
      </label>

      <label className="field">
        <span>Occasion</span>
        <select
          value={values.occasion}
          onChange={(event) => onChange('occasion', event.target.value)}
          disabled={disabled}
          required
          aria-invalid={Boolean(errors.occasion)}
        >
          <option value="">Select occasion</option>
          {OCCASIONS.map((occasion) => (
            <option key={occasion} value={occasion}>
              {occasion}
            </option>
          ))}
        </select>
        {errors.occasion && <small role="alert">{errors.occasion}</small>}
      </label>

      <label className="field">
        <span>Subcategory</span>
        <input
          value={values.subcategory}
          onChange={(event) => onChange('subcategory', event.target.value)}
          disabled={disabled}
          maxLength={80}
          placeholder="Optional, such as knit or loafer"
        />
      </label>

      <label className="field">
        <span>Secondary colour</span>
        <input
          value={values.secondary_colour}
          onChange={(event) => onChange('secondary_colour', event.target.value)}
          disabled={disabled}
          maxLength={40}
          placeholder="Optional"
        />
      </label>

      <label className="field">
        <span>Brand</span>
        <input
          value={values.brand}
          onChange={(event) => onChange('brand', event.target.value)}
          disabled={disabled}
          maxLength={80}
          placeholder="Optional"
        />
      </label>

      <label className="field">
        <span>Season</span>
        <select
          value={values.season}
          onChange={(event) => onChange('season', event.target.value)}
          disabled={disabled}
        >
          <option value="">Not specified</option>
          {SEASONS.map((season) => (
            <option key={season} value={season}>
              {season}
            </option>
          ))}
        </select>
      </label>

      <label className="field field-wide">
        <span>Notes</span>
        <textarea
          value={values.notes}
          onChange={(event) => onChange('notes', event.target.value)}
          disabled={disabled}
          maxLength={2000}
          rows={3}
          placeholder="Optional fit, fabric, or care notes"
          aria-invalid={Boolean(errors.notes)}
        />
        {errors.notes && <small role="alert">{errors.notes}</small>}
      </label>
    </div>
  );
}
