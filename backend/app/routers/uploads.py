from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_csrf
from app.models import User
from app.schemas import DiscardUpload, SignatureResponse
from app.services.cloudinary_service import sign_upload
from app.services.item_service import discard_upload

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/signature", response_model=SignatureResponse)
def create_signature(
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
) -> SignatureResponse:
    signed = sign_upload(user.id)
    return SignatureResponse(
        signature=signed.signature,
        timestamp=signed.timestamp,
        api_key=signed.api_key,
        cloud_name=signed.cloud_name,
        folder=signed.folder,
        allowed_formats=signed.allowed_formats,
        upload_url=signed.upload_url,
    )


@router.post("/discard", status_code=204)
def discard(
    payload: DiscardUpload,
    user: User = Depends(get_current_user),
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> None:
    discard_upload(db, payload.public_id, user.id)
