"""Signed Cloudinary uploads and asset checks.

The API secret is used only in this module. Callers receive a signature,
the public API key, and the cloud name. They never receive the secret.

Deletion strategy
-----------------
Removing a clothing item deletes the Cloudinary asset first, then the
database row.

- If Cloudinary reports ``ok`` or ``not found``, the database row is deleted.
  ``not found`` means the asset is already gone, so the row should not remain.
- If Cloudinary raises or returns any other result, the database row is kept
  and the request fails. A temporary Cloudinary outage therefore does not
  remove the wardrobe record, and the user can retry.
- The remaining edge is a database failure after Cloudinary has already
  deleted the file. That is logged with the public id and returned as an
  error. Preferring this order avoids orphaned Cloudinary assets when the
  network call fails, which is the more common failure.
"""

import logging
import time
from dataclasses import dataclass

import cloudinary
import cloudinary.api
import cloudinary.uploader
import cloudinary.utils
from cloudinary.exceptions import NotFound

from app.config import get_settings
from app.constants import ALLOWED_FORMATS, ALLOWED_FORMATS_PARAM, MAX_UPLOAD_BYTES
from app.errors import CloudinaryNotConfigured, CloudinaryUnavailable, InvalidAsset

logger = logging.getLogger("wardrobeai.cloudinary")


@dataclass(frozen=True)
class VerifiedAsset:
    public_id: str
    secure_url: str
    bytes: int
    format: str


@dataclass(frozen=True)
class UploadSignature:
    signature: str
    timestamp: int
    api_key: str
    cloud_name: str
    folder: str
    allowed_formats: str
    upload_url: str


def is_configured() -> bool:
    return get_settings().cloudinary_configured


def _configure() -> None:
    settings = get_settings()
    if not settings.cloudinary_configured:
        raise CloudinaryNotConfigured()
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name.strip(),
        api_key=settings.cloudinary_api_key.strip(),
        api_secret=settings.cloudinary_api_secret.strip(),
        secure=True,
    )


def user_upload_folder(user_id: int) -> str:
    return f"wardrobeai/users/{user_id}/clothing"


def sign_upload(user_id: int) -> UploadSignature:
    """Sign the exact parameters the browser must send to Cloudinary."""
    _configure()
    settings = get_settings()
    timestamp = int(time.time())
    params_to_sign = {
        "timestamp": timestamp,
        "folder": user_upload_folder(user_id),
        "allowed_formats": ALLOWED_FORMATS_PARAM,
    }
    signature = cloudinary.utils.api_sign_request(
        params_to_sign,
        settings.cloudinary_api_secret.strip(),
    )
    cloud_name = settings.cloudinary_cloud_name.strip()
    folder = user_upload_folder(user_id)
    logger.info("Issued upload signature for user %s", user_id)
    return UploadSignature(
        signature=signature,
        timestamp=timestamp,
        api_key=settings.cloudinary_api_key.strip(),
        cloud_name=cloud_name,
        folder=folder,
        allowed_formats=ALLOWED_FORMATS_PARAM,
        upload_url=f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
    )


def verify_asset(public_id: str, user_id: int) -> VerifiedAsset:
    """Confirm the asset exists in this Cloudinary account before saving it.

    The secure URL stored in the database comes from Cloudinary's Admin API,
    not from the value supplied by the browser.
    """
    if not public_id.startswith(f"{user_upload_folder(user_id)}/"):
        raise InvalidAsset("Image identifier is not a WardrobeAI Cloudinary asset.")
    _configure()
    settings = get_settings()

    try:
        info = cloudinary.api.resource(public_id, resource_type="image")
    except NotFound as exc:
        logger.info("Cloudinary asset not found: %s", public_id)
        raise InvalidAsset("The uploaded image could not be found in Cloudinary.") from exc
    except Exception as exc:
        logger.exception("Cloudinary verification failed for %s", public_id)
        raise CloudinaryUnavailable() from exc

    asset_format = str(info.get("format") or "").lower()
    if asset_format == "jpeg":
        asset_format = "jpg"
    if asset_format not in ALLOWED_FORMATS:
        raise InvalidAsset("Only JPEG, PNG, and WebP images are accepted.")

    size = int(info.get("bytes") or 0)
    if size <= 0 or size > MAX_UPLOAD_BYTES:
        raise InvalidAsset("Image must be a JPEG, PNG, or WebP file up to 10 MB.")

    secure_url = str(info.get("secure_url") or "")
    cloud_name = settings.cloudinary_cloud_name.strip()
    expected_prefix = f"https://res.cloudinary.com/{cloud_name}/"
    if not secure_url.startswith(expected_prefix):
        raise InvalidAsset("Cloudinary did not return a URL for this account.")

    confirmed_id = str(info.get("public_id") or "")
    if confirmed_id != public_id:
        raise InvalidAsset("Cloudinary asset identifier did not match the upload.")

    return VerifiedAsset(
        public_id=confirmed_id,
        secure_url=secure_url,
        bytes=size,
        format=asset_format,
    )


def destroy_asset(public_id: str, user_id: int) -> str:
    """Delete an asset. Returns ``ok`` or ``not found``.

    Any other outcome raises and must not be followed by a database delete.
    """
    _configure()
    if not public_id.startswith(f"{user_upload_folder(user_id)}/"):
        raise InvalidAsset("Image identifier is not a WardrobeAI Cloudinary asset.")
    try:
        result = cloudinary.uploader.destroy(
            public_id,
            resource_type="image",
            invalidate=True,
        )
    except Exception as exc:
        logger.exception("Cloudinary deletion failed for %s", public_id)
        raise CloudinaryUnavailable(
            "The clothing image could not be deleted from Cloudinary. The wardrobe item was kept."
        ) from exc

    outcome = str(result.get("result") or "")
    if outcome not in {"ok", "not found"}:
        logger.error("Unexpected Cloudinary destroy result for %s: %s", public_id, outcome)
        raise CloudinaryUnavailable(
            "The clothing image could not be deleted from Cloudinary. The wardrobe item was kept."
        )
    logger.info("Cloudinary destroy %s for %s", outcome, public_id)
    return outcome
