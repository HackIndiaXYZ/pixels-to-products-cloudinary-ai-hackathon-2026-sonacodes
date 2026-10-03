import { ACCEPTED_IMAGE_TYPES, MAX_UPLOAD_BYTES } from '../constants';
import type { UploadSignature } from '../types';

export interface DirectUploadResult {
  public_id: string;
  secure_url: string;
}

const EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

export function validateImageFile(file: File): string | null {
  const extension = file.name.includes('.')
    ? file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
    : '';
  const typeAllowed = ACCEPTED_IMAGE_TYPES.includes(
    file.type as (typeof ACCEPTED_IMAGE_TYPES)[number],
  );
  const extensionAllowed = EXTENSIONS.includes(extension);
  if (!typeAllowed && !extensionAllowed) {
    return 'Use a JPEG, PNG, or WebP photograph.';
  }
  if (file.size <= 0 || file.size > MAX_UPLOAD_BYTES) {
    return 'Photographs must be 10 MB or smaller.';
  }
  return null;
}

function isUploadResult(value: unknown): value is DirectUploadResult & {
  format?: string;
  bytes?: number;
  resource_type?: string;
} {
  if (!value || typeof value !== 'object') return false;
  const record = value as Record<string, unknown>;
  return typeof record.public_id === 'string' && typeof record.secure_url === 'string';
}

export function uploadToCloudinary(
  file: File,
  signature: UploadSignature,
  onProgress: (percent: number) => void,
): Promise<DirectUploadResult> {
  const form = new FormData();
  form.append('file', file);
  form.append('api_key', signature.api_key);
  form.append('timestamp', String(signature.timestamp));
  form.append('signature', signature.signature);
  form.append('folder', signature.folder);
  form.append('allowed_formats', signature.allowed_formats);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', signature.upload_url);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onerror = () => reject(new Error('The photograph could not be uploaded to Cloudinary.'));
    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText) as unknown;
      } catch {
        body = null;
      }
      if (xhr.status < 200 || xhr.status >= 300) {
        const message =
          body &&
          typeof body === 'object' &&
          'error' in body &&
          body.error &&
          typeof body.error === 'object' &&
          'message' in body.error &&
          typeof body.error.message === 'string'
            ? body.error.message
            : 'Cloudinary rejected the photograph.';
        reject(new Error(message));
        return;
      }
      if (!isUploadResult(body)) {
        reject(new Error('Cloudinary returned an unexpected upload response.'));
        return;
      }
      if (!body.public_id.startsWith(`${signature.folder}/`)) {
        reject(new Error('Cloudinary stored the photograph outside the wardrobe folder.'));
        return;
      }
      const expectedUrl = `https://res.cloudinary.com/${signature.cloud_name}/`;
      if (!body.secure_url.startsWith(expectedUrl)) {
        reject(new Error('Cloudinary returned an unexpected image URL.'));
        return;
      }
      if (body.resource_type && body.resource_type !== 'image') {
        reject(new Error('Only photographs can be added to the wardrobe.'));
        return;
      }
      const format = (body.format || '').toLowerCase();
      if (format && !['jpg', 'jpeg', 'png', 'webp'].includes(format)) {
        reject(new Error('Use a JPEG, PNG, or WebP photograph.'));
        return;
      }
      if (typeof body.bytes === 'number' && body.bytes > MAX_UPLOAD_BYTES) {
        reject(new Error('Photographs must be 10 MB or smaller.'));
        return;
      }
      onProgress(100);
      resolve({ public_id: body.public_id, secure_url: body.secure_url });
    };
    xhr.send(form);
  });
}
