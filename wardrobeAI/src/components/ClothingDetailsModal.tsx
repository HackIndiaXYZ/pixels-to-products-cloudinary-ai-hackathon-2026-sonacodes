import { useEffect, useId, useState, type FormEvent } from 'react';
import type { Cloudinary } from '@cloudinary/url-gen';
import { ApiError, deleteItem, fetchItem, updateItem } from '../api/client';
import { ClothingImage } from '../cloudinary/images';
import { validateClothingFields } from '../clothingForm';
import { ClothingFields } from './ClothingFields';
import {
  formValuesFromItem,
  type ClothingFormValues,
  type ClothingItem,
} from '../types';

interface ClothingDetailsModalProps {
  itemId: number;
  cld: Cloudinary | null;
  onClose: () => void;
  onUpdated: (item: ClothingItem) => void;
  onDeleted: (itemId: number) => void;
}

function detailRows(item: ClothingItem): Array<[string, string]> {
  return [
    ['Category', item.category],
    ['Subcategory', item.subcategory || '—'],
    ['Colour', item.colour],
    ['Secondary colour', item.secondary_colour || '—'],
    ['Pattern', item.pattern],
    ['Style', item.style],
    ['Occasion', item.occasion],
    ['Season', item.season || '—'],
    ['Brand', item.brand || '—'],
    ['Notes', item.notes || '—'],
  ];
}

export function ClothingDetailsModal({
  itemId,
  cld,
  onClose,
  onUpdated,
  onDeleted,
}: ClothingDetailsModalProps) {
  const titleId = useId();
  const [item, setItem] = useState<ClothingItem | null>(null);
  const [editing, setEditing] = useState(false);
  const [values, setValues] = useState<ClothingFormValues | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  useEffect(() => {
    let active = true;
    fetchItem(itemId)
      .then((next) => {
        if (!active) return;
        setItem(next);
        setValues(formValuesFromItem(next));
      })
      .catch((error: unknown) => {
        if (!active) return;
        setLoadError(error instanceof ApiError ? error.message : 'This piece could not be opened.');
      });
    return () => {
      active = false;
    };
  }, [itemId]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape' && !busy) onClose();
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [busy, onClose]);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!values || busy) return;
    const nextErrors = validateClothingFields(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    setBusy(true);
    setFormError(null);
    try {
      const updated = await updateItem(itemId, values);
      setItem(updated);
      setValues(formValuesFromItem(updated));
      setEditing(false);
      onUpdated(updated);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : 'The changes could not be saved.');
    } finally {
      setBusy(false);
    }
  }

  async function handleDelete() {
    if (busy) return;
    setBusy(true);
    setFormError(null);
    try {
      await deleteItem(itemId);
      onDeleted(itemId);
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : 'This piece could not be deleted.');
      setBusy(false);
      setConfirmingDelete(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={() => { if (!busy) onClose(); }}>
      <div
        className="modal modal-detail"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="modal-header">
          <div>
            <p className="eyebrow">Piece</p>
            <h2 id={titleId}>{item?.name ?? 'Clothing details'}</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose} disabled={busy} aria-label="Close">
            ×
          </button>
        </header>

        {loadError && (
          <p className="form-error" role="alert">
            {loadError}
          </p>
        )}
        {!item && !loadError && <p className="muted">Loading piece…</p>}

        {item && values && (
          <div className="detail-layout">
            <ClothingImage
              cld={cld}
              publicId={item.cloudinary_public_id}
              secureUrl={item.secure_url}
              alt={item.name}
              width={720}
              height={960}
            />
            {editing ? (
              <form onSubmit={handleSave}>
                {formError && (
                  <p className="form-error" role="alert">
                    {formError}
                  </p>
                )}
                <ClothingFields
                  values={values}
                  errors={errors}
                  disabled={busy}
                  onChange={(field, value) =>
                    setValues((current) => (current ? { ...current, [field]: value } : current))
                  }
                />
                <div className="modal-actions">
                  <button
                    type="button"
                    className="button ghost"
                    disabled={busy}
                    onClick={() => {
                      setEditing(false);
                      setValues(formValuesFromItem(item));
                      setErrors({});
                      setFormError(null);
                    }}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="button" disabled={busy}>
                    {busy ? 'Saving…' : 'Save changes'}
                  </button>
                </div>
              </form>
            ) : (
              <div>
                {formError && (
                  <p className="form-error" role="alert">
                    {formError}
                  </p>
                )}
                <dl className="detail-list">
                  {detailRows(item).map(([label, value]) => (
                    <div key={label}>
                      <dt>{label}</dt>
                      <dd>{value}</dd>
                    </div>
                  ))}
                </dl>
                {confirmingDelete ? (
                  <div className="confirm-box">
                    <p>Remove this piece from your wardrobe? The photograph will be deleted too.</p>
                    <div className="modal-actions">
                      <button
                        type="button"
                        className="button ghost"
                        disabled={busy}
                        onClick={() => setConfirmingDelete(false)}
                      >
                        Keep
                      </button>
                      <button type="button" className="button danger" disabled={busy} onClick={handleDelete}>
                        {busy ? 'Removing…' : 'Delete piece'}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="modal-actions">
                    <button type="button" className="button danger ghost-danger" onClick={() => setConfirmingDelete(true)}>
                      Delete
                    </button>
                    <button type="button" className="button" onClick={() => setEditing(true)}>
                      Edit details
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
