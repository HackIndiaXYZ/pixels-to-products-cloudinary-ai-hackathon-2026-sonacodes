import type { Cloudinary } from '@cloudinary/url-gen';

interface ClothingImageProps {
  cld: Cloudinary | null;
  publicId: string;
  secureUrl: string;
  alt: string;
  width: number;
  height: number;
}

export function ClothingImage({
  secureUrl,
  alt,
  width,
  height,
}: ClothingImageProps) {
  if (!secureUrl) return <div className="photo-fallback" role="img" aria-label={alt} />;
  return (
    <img
      src={secureUrl}
      alt={alt}
      width={width}
      height={height}
      className="photo"
    />
  );
}
