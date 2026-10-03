export const CATEGORIES = [
  'Tops',
  'Bottoms',
  'Dresses',
  'Outerwear',
  'Shoes',
  'Accessories',
  'Bags',
] as const;

export const PATTERNS = [
  'Solid',
  'Striped',
  'Checked',
  'Floral',
  'Polka dot',
  'Graphic',
  'Textured',
  'Animal print',
  'Other',
] as const;

export const STYLES = [
  'Casual',
  'Smart casual',
  'Formal',
  'Minimal',
  'Classic',
  'Sporty',
  'Bohemian',
  'Streetwear',
] as const;

export const OCCASIONS = [
  'Everyday',
  'Work',
  'Evening',
  'Weekend',
  'Travel',
  'Special occasion',
] as const;

export const SEASONS = ['Spring', 'Summer', 'Autumn', 'Winter', 'All seasons'] as const;

export const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export const ACCEPTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'] as const;
