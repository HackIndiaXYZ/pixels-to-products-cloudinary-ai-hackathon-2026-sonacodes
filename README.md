# WardrobeAI

WardrobeAI is a personal digital wardrobe with cookie-based accounts, Cloudinary image storage, clothing recognition, and wardrobe-scoped outfit recommendations. Public visitors can explore the landing page and create an account; each signed-in user has an isolated closet.

## Run the API

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Fill `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` in `backend/.env`. Do not commit that file. The API secret stays on the server.

For local development, keep `COOKIE_SECURE=false`. For HTTPS production set `COOKIE_SECURE=true`, configure exact `CORS_ORIGINS`, and use a persistent database. See [backend/README.md](backend/README.md) for auth API and deployment details.

## Run the app

```bash
cd wardrobeAI
npm install
npm run dev
```

Open http://localhost:5173. Visitors land on the public home page; registration and sign-in lead to the protected `/app` wardrobe. Vite proxies `/api` to http://127.0.0.1:8000.

The app backs up the existing development SQLite database before the auth schema update. Existing clothing rows are retained with no owner and are not exposed to any newly registered user. Legacy Cloudinary files remain untouched.

Optional frontend variables are listed in `wardrobeAI/.env.example`. The cloud name can come from the API, so the frontend does not need Cloudinary credentials to display images.

## Checks

```bash
cd backend && .venv/bin/pytest
cd wardrobeAI && npm run build
```
