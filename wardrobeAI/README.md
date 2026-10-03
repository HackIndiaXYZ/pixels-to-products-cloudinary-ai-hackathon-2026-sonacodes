# WardrobeAI

React + Vite closet for WardrobeAI. Photographs upload directly from the browser to Cloudinary using a signature from the FastAPI backend. Clothing details are saved through `/api/items`.

The original unsigned upload widget remains in `src/cloudinary/UploadWidget.tsx`. The wardrobe uses signed uploads instead, so the Cloudinary API secret is never shipped to the browser.

## Setup

```bash
npm install
npm run dev
```

Start the API first. See the repository README and `backend/README.md`.

`VITE_CLOUDINARY_CLOUD_NAME` is optional when the backend health check returns the cloud name. `VITE_API_BASE_URL` can stay empty during local development because Vite proxies `/api` to port 8000.

Copy `.env.example` to `.env` only if you need to override those values. Restart the dev server after changing `.env`.
