import type { ClothingFormValues } from './types';

export function validateClothingFields(values: ClothingFormValues): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!values.name.trim()) errors.name = 'Enter a name.';
  else if (values.name.trim().length > 80) errors.name = 'Use 80 characters or fewer.';
  if (!values.category) errors.category = 'Choose a category.';
  if (!values.colour.trim()) errors.colour = 'Enter a colour.';
  else if (values.colour.trim().length > 40) errors.colour = 'Use 40 characters or fewer.';
  if (!values.pattern) errors.pattern = 'Choose a pattern.';
  if (!values.style) errors.style = 'Choose a style.';
  if (!values.occasion) errors.occasion = 'Choose an occasion.';
  if (values.notes.trim().length > 2000) errors.notes = 'Notes must be 2000 characters or fewer.';
  return errors;
}
