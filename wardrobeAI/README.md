# WardrobeAI

React + Vite closet for WardrobeAI. Photographs upload directly from the browser to Cloudinary using a signature from the FastAPI backend. Clothing details are saved through `/api/items`.

The original unsigned upload widget remains in `src/cloudinary/UploadWidget.tsx`. The wardrobe uses signed uploads instead, so the Cloudinary API secret is never shipped to the browser.

## Setup

On a fresh checkout, create `.env` from `.env.example` before starting the frontend so `VITE_API_URL` points to the local API.

```bash
npm install
npm run dev
```

Start the API first. See the repository README and `backend/README.md`.

`VITE_CLOUDINARY_CLOUD_NAME` is optional when the backend health check returns the cloud name. Set `VITE_API_URL` in `.env` to the backend origin (the example uses `http://localhost:8000`). For a separately hosted frontend, use the deployed backend origin; Render's Blueprint configures it from the backend service host.

Restart the dev server after changing `.env`.
