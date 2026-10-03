"""Shared wardrobe vocabulary and Cloudinary upload limits."""

UPLOAD_FOLDER = "wardrobeai/items"
ALLOWED_FORMATS = ("jpg", "png", "webp")
ALLOWED_FORMATS_PARAM = "jpg,png,webp"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

CATEGORIES = (
    "Tops",
    "Bottoms",
    "Dresses",
    "Outerwear",
    "Shoes",
    "Accessories",
    "Bags",
)

PATTERNS = (
    "Solid",
    "Striped",
    "Checked",
    "Floral",
    "Polka dot",
    "Graphic",
    "Textured",
    "Animal print",
    "Other",
)

STYLES = (
    "Casual",
    "Smart casual",
    "Formal",
    "Minimal",
    "Classic",
    "Sporty",
    "Bohemian",
    "Streetwear",
)

OCCASIONS = (
    "Everyday",
    "Work",
    "Evening",
    "Weekend",
    "Travel",
    "Special occasion",
)

SEASONS = (
    "Spring",
    "Summer",
    "Autumn",
    "Winter",
    "All seasons",
)

SORTS = ("recent", "oldest", "name")
