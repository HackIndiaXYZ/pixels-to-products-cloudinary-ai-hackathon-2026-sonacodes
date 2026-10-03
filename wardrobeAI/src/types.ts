export interface ClothingItem {
  id: number;
  name: string;
  category: string;
  subcategory: string | null;
  colour: string;
  secondary_colour: string | null;
  pattern: string;
  style: string;
  occasion: string;
  season: string | null;
  brand: string | null;
  notes: string | null;
  material?: string | null;
  texture?: string | null;
  sleeve_type?: string | null;
  neckline?: string | null;
  fit?: string | null;
  length?: string | null;
  formality?: string | null;
  ai_description?: string | null;
  ai_tags?: string | null;
  recognition_confidence?: number | null;
  recognition_provider?: string | null;
  recognition_status?: string | null;
  cloudinary_public_id: string;
  secure_url: string;
  created_at: string;
  updated_at: string;
}

export interface ItemPage {
  items: ClothingItem[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface WardrobeStats {
  total_items: number;
  category_count: number;
  top_category: string | null;
  top_category_count: number;
  recent_items: ClothingItem[];
  colours: string[];
}

export interface HealthResponse {
  status: string;
  database: string;
  cloudinary_configured: boolean;
  cloud_name: string | null;
}

export interface UploadSignature {
  signature: string;
  timestamp: number;
  api_key: string;
  cloud_name: string;
  folder: string;
  allowed_formats: string;
  upload_url: string;
}

export interface ClothingFormValues {
  name: string;
  category: string;
  subcategory: string;
  colour: string;
  secondary_colour: string;
  pattern: string;
  style: string;
  occasion: string;
  season: string;
  brand: string;
  notes: string;
}

export interface ItemQuery {
  q: string;
  category: string;
  colour: string;
  pattern: string;
  style: string;
  occasion: string;
  sort: 'recent' | 'oldest' | 'name';
  page: number;
  pageSize: number;
}

export interface AIRecognitionResponse {
  success: boolean;
  recognition: Record<string, unknown>;
  provider: string;
}

export interface AIRecommendationRequest {
  occasion?: string;
  preferred_style?: string;
  preferred_colours?: string[];
  avoid_colours?: string[];
  season?: string;
  weather?: Record<string, unknown> | null;
  include_item_ids?: number[];
  exclude_item_ids?: number[];
}

export interface AIRecommendationItem {
  id: number;
  name: string;
  category: string;
  colour: string;
  secure_url: string;
}

export interface AIRecommendation {
  title: string;
  description: string;
  occasion: string;
  style: string;
  items: AIRecommendationItem[];
  composition_url?: string;
  styling_tips: string[];
  reasoning: string;
  compatibility_score: number;
}

export interface AIRecommendationResponse {
  success: boolean;
  recommendations: AIRecommendation[];
  provider?: string;
  warning?: string;
}

export const emptyClothingForm = (): ClothingFormValues => ({
  name: '',
  category: '',
  subcategory: '',
  colour: '',
  secondary_colour: '',
  pattern: '',
  style: '',
  occasion: '',
  season: '',
  brand: '',
  notes: '',
});

export function formValuesFromItem(item: ClothingItem): ClothingFormValues {
  return {
    name: item.name,
    category: item.category,
    subcategory: item.subcategory ?? '',
    colour: item.colour,
    secondary_colour: item.secondary_colour ?? '',
    pattern: item.pattern,
    style: item.style,
    occasion: item.occasion,
    season: item.season ?? '',
    brand: item.brand ?? '',
    notes: item.notes ?? '',
  };
}
