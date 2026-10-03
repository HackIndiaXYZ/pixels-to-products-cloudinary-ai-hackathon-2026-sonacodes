import { Cloudinary } from '@cloudinary/url-gen';

// Vite only exposes variables prefixed with VITE_. The API secret never belongs here.
const cloudNameFromEnv = import.meta.env.VITE_CLOUDINARY_CLOUD_NAME || '';

export const uploadPreset = import.meta.env.VITE_CLOUDINARY_UPLOAD_PRESET || '';

export function createCloudinary(cloudName: string) {
  return new Cloudinary({
    cloud: {
      cloudName,
    },
  });
}

// Null when the cloud name is only known from the API health response.
export const cld = cloudNameFromEnv ? createCloudinary(cloudNameFromEnv) : null;
export const cloudName = cloudNameFromEnv;
