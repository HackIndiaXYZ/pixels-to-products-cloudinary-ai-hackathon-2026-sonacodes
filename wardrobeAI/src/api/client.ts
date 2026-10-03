import type {
  AIRecommendationRequest,
  AIRecommendationResponse,
  AIRecognitionResponse,
  ClothingFormValues,
  ClothingItem,
  HealthResponse,
  ItemPage,
  ItemQuery,
  UploadSignature,
  WardrobeStats,
} from '../types';

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim() ?? '';
const API_BASE = configuredApiUrl
  ? `${/^https?:\/\//i.test(configuredApiUrl) ? '' : 'https://'}${configuredApiUrl}`.replace(/\/+$/, '')
  : '';
let csrfToken = '';

export function setCsrfToken(token: string) {
  csrfToken = token;
}

export class ApiError extends Error {
  status: number;
  code: string;
  fields: Record<string, string>;

  constructor(
    message: string,
    status: number,
    code: string,
    fields: Record<string, string> = {},
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

interface ErrorPayload {
  error?: {
    code?: string;
    message?: string;
    fields?: Record<string, string>;
  };
}

async function parseError(response: Response): Promise<ApiError> {
  let payload: ErrorPayload | null = null;
  try {
    payload = (await response.json()) as ErrorPayload;
  } catch {
    payload = null;
  }
  const body = payload as (ErrorPayload & { detail?: string }) | null;
  return new ApiError(
    payload?.error?.message || body?.detail || 'The wardrobe request failed.',
    response.status,
    payload?.error?.code || 'request_failed',
    payload?.error?.fields || {},
  );
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { credentials: 'include', ...init });
  } catch {
    throw new ApiError(
      'Cannot reach the WardrobeAI API. Start the backend and try again.',
      0,
      'network_error',
    );
  }
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/api/auth/')) {
      window.dispatchEvent(new Event('wardrobeai:unauthorized'));
    }
    throw await parseError(response);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function jsonRequest<T>(path: string, method: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (csrfToken) headers['X-CSRF-Token'] = csrfToken;
  return request<T>(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export interface UserProfile {
  id: number;
  name: string;
  email: string;
  created_at: string;
}

interface AuthPayload {
  user: UserProfile;
  csrf_token: string;
}

export function fetchCsrf(): Promise<{ csrf_token: string }> {
  return request('/api/auth/csrf');
}

export function fetchCurrentUser(): Promise<UserProfile> {
  return request('/api/auth/me');
}

export async function registerAccount(payload: {
  name: string;
  email: string;
  password: string;
  confirm_password: string;
}): Promise<UserProfile> {
  const response = await jsonRequest<AuthPayload>('/api/auth/register', 'POST', payload);
  setCsrfToken(response.csrf_token);
  return response.user;
}

export async function loginAccount(payload: { email: string; password: string }): Promise<UserProfile> {
  const response = await jsonRequest<AuthPayload>('/api/auth/login', 'POST', payload);
  setCsrfToken(response.csrf_token);
  return response.user;
}

export async function logoutAccount(): Promise<void> {
  await request<void>('/api/auth/logout', {
    method: 'POST',
    headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
  });
  csrfToken = '';
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health');
}

export function fetchStats(): Promise<WardrobeStats> {
  return request<WardrobeStats>('/api/stats');
}

export function fetchItems(query: ItemQuery): Promise<ItemPage> {
  const params = new URLSearchParams();
  if (query.q.trim()) params.set('q', query.q.trim());
  if (query.category) params.set('category', query.category);
  if (query.colour) params.set('colour', query.colour);
  if (query.pattern) params.set('pattern', query.pattern);
  if (query.style) params.set('style', query.style);
  if (query.occasion) params.set('occasion', query.occasion);
  params.set('sort', query.sort);
  params.set('page', String(query.page));
  params.set('page_size', String(query.pageSize));
  return request<ItemPage>(`/api/items?${params.toString()}`);
}

export function fetchItem(itemId: number): Promise<ClothingItem> {
  return request<ClothingItem>(`/api/items/${itemId}`);
}

function clothingPayload(values: ClothingFormValues, publicId?: string) {
  return {
    name: values.name.trim(),
    category: values.category,
    subcategory: values.subcategory.trim() || null,
    colour: values.colour.trim(),
    secondary_colour: values.secondary_colour.trim() || null,
    pattern: values.pattern,
    style: values.style,
    occasion: values.occasion,
    season: values.season || null,
    brand: values.brand.trim() || null,
    notes: values.notes.trim() || null,
    ...(publicId ? { cloudinary_public_id: publicId } : {}),
  };
}

export function createItem(values: ClothingFormValues, publicId: string): Promise<ClothingItem> {
  return jsonRequest<ClothingItem>('/api/items', 'POST', clothingPayload(values, publicId));
}

export function updateItem(itemId: number, values: ClothingFormValues): Promise<ClothingItem> {
  return jsonRequest<ClothingItem>(`/api/items/${itemId}`, 'PUT', clothingPayload(values));
}

export function deleteItem(itemId: number): Promise<void> {
  return request<void>(`/api/items/${itemId}`, { method: 'DELETE' });
}

export function requestUploadSignature(): Promise<UploadSignature> {
  return jsonRequest<UploadSignature>('/api/uploads/signature', 'POST');
}

export function discardUpload(publicId: string): Promise<void> {
  return jsonRequest<void>('/api/uploads/discard', 'POST', { public_id: publicId });
}

export function recognizeClothing(publicId: string, secureUrl: string): Promise<AIRecognitionResponse> {
  return jsonRequest<AIRecognitionResponse>('/api/ai/recognize-clothing', 'POST', {
    cloudinary_public_id: publicId,
    secure_url: secureUrl,
  });
}

export function recommendOutfits(payload: AIRecommendationRequest): Promise<AIRecommendationResponse> {
  return jsonRequest<AIRecommendationResponse>('/api/ai/recommend-outfits', 'POST', payload);
}
