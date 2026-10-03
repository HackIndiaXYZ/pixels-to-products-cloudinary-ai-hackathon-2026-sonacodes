"""Application errors returned to the client without internal details."""


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "error") -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code


class CloudinaryNotConfigured(AppError):
    def __init__(self) -> None:
        super().__init__(
            "Cloudinary is not configured. Add CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET to backend/.env.",
            status_code=503,
            code="cloudinary_not_configured",
        )


class CloudinaryUnavailable(AppError):
    def __init__(self, message: str = "Cloudinary could not be reached. Try again.") -> None:
        super().__init__(message, status_code=502, code="cloudinary_unavailable")


class InvalidAsset(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400, code="invalid_asset")


class NotFoundError(AppError):
    def __init__(self, message: str = "Clothing item not found.") -> None:
        super().__init__(message, status_code=404, code="not_found")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=409, code="conflict")
