import { useEffect, useId, useRef, useState, type FormEvent } from 'react';
import { ApiError, createItem, discardUpload, requestUploadSignature } from '../api/client';
import { uploadToCloudinary, validateImageFile } from '../api/cloudinaryUpload';
import { validateClothingFields } from '../clothingForm';
import { ClothingFields } from './ClothingFields';
import { emptyClothingForm, type ClothingFormValues, type ClothingItem } from '../types';

interface UploadClothingModalProps {
  onClose: () => void;
  onCreated: (item: ClothingItem) => void;
}

export function UploadClothingModal({ onClose, onCreated }: UploadClothingModalProps) {
  const titleId = useId();
  const fileRef = useRef<HTMLInputElement>(null);
  const [values, setValues] = useState<ClothingFormValues>(emptyClothingForm);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape' && !submitting) onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose, submitting]);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  function chooseFile(next: File | null) {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    if (!next) {
      setFile(null);
      setPreviewUrl(null);
      return;
    }
    const message = validateImageFile(next);
    if (message) {
      setErrors((current) => ({ ...current, image: message }));
      setFile(null);
      setPreviewUrl(null);
      return;
    }
    setErrors((current) => {
      const nextErrors = { ...current };
      delete nextErrors.image;
      return nextErrors;
    });
    setFile(next);
    setPreviewUrl(URL.createObjectURL(next));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (submitting) return;
    const nextErrors = validateClothingFields(values);
    if (!file) nextErrors.image = 'Choose a photograph.';
    setErrors(nextErrors);
    setFormError(null);
    if (Object.keys(nextErrors).length > 0 || !file) return;

    setSubmitting(true);
    setProgress(0);
    let publicId: string | null = null;
    try {
      const signature = await requestUploadSignature();
      const uploaded = await uploadToCloudinary(file, signature, setProgress);
      publicId = uploaded.public_id;
      const item = await createItem(values, uploaded.public_id);
      onCreated(item);
    } catch (error) {
      let message = error instanceof Error ? error.message : 'The upload failed.';
      if (error instanceof ApiError && error.code === 'cloudinary_not_configured') {
        message = error.message;
      }
      if (publicId) {
        try {
          await discardUpload(publicId);
          message = `${message} The photograph was removed from Cloudinary.`;
        } catch {
          message = `${message} The photograph may still be stored in Cloudinary.`;
        }
      }
      setFormError(message);
      setSubmitting(false);
      setProgress(0);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={() => { if (!submitting) onClose(); }}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="eyebrow">New piece</p>
            <h2 id={titleId}>Add to wardrobe</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} disabled={submitting} aria-label="Close">
            ×
          </button>
        </header>
        <form onSubmit={handleSubmit}>
          {formError && (
            <p className="form-error" role="alert">
              {formError}
            </p>
          )}
          <div className="upload-picker">
            {previewUrl ? (
              <img src={previewUrl} alt="Selected clothing preview" className="preview" />
            ) : (
              <div className="preview preview-empty">Photograph</div>
            )}
            <div className="upload-actions">
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="visually-hidden"
                onChange={(event) => chooseFile(event.target.files?.[0] ?? null)}
                disabled={submitting}
              />
              <button type="button" className="button secondary" onClick={() => fileRef.current?.click()} disabled={submitting}>
                {file ? 'Replace photograph' : 'Choose photograph'}
              </button>
              {file && (
                <button
                  type="button"
                  className="button ghost"
                  disabled={submitting}
                  onClick={() => {
                    if (fileRef.current) fileRef.current.value = '';
                    chooseFile(null);
                  }}
                >
                  Remove
                </button>
              )}
              <p className="muted">JPEG, PNG, or WebP up to 10 MB.</p>
              {errors.image && <small role="alert">{errors.image}</small>}
            </div>
          </div>
          {submitting && (
            <div className="progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress} role="progressbar">
              <span style={{ width: `${progress}%` }} />
            </div>
          )}
          <ClothingFields
            values={values}
            errors={errors}
            disabled={submitting}
            onChange={(field, value) => setValues((current) => ({ ...current, [field]: value }))}
          />
          <div className="modal-actions">
            <button type="button" className="button ghost" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="button" disabled={submitting}>
              {submitting ? 'Adding…' : 'Add to wardrobe'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
