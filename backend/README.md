# WardrobeAI API

FastAPI service for the digital wardrobe. Images are uploaded from the browser directly to Cloudinary with a signature generated here. The Cloudinary API secret never leaves this process.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

| Variable | Required | Purpose |
| --- | --- | --- |
| `CLOUDINARY_CLOUD_NAME` | Yes, for uploads | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Yes, for uploads | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Yes, for uploads | Cloudinary API secret. Server only. |
| `DATABASE_URL` | No | Defaults to SQLite at `backend/data/wardrobe.db` |
| `CORS_ORIGINS` | No | Defaults to the Vite dev and preview origins |
| `COOKIE_SECURE` | No | Set `true` in HTTPS production; defaults to `false` for local development |
| `COOKIE_SAME_SITE` | No | `lax` by default; use `none` with `COOKIE_SECURE=true` only for cross-site deployments |
| `SESSION_TTL_HOURS` | No | Session lifetime, defaults to 168 hours |

For PostgreSQL deployments, `psycopg[binary]` is installed from requirements and Render `postgresql://` URLs are normalized to `postgresql+psycopg://`.

The API starts even when Cloudinary credentials are missing. `GET /api/health` then reports `cloudinary_configured: false`, and upload or delete requests return `503` without changing the database.

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The Render production start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Both `/health` (Render health check) and `/api/health` (application health) are available.

Tables are created on startup. Existing SQLite wardrobe rows are migrated with a nullable `user_id`; they remain unowned and are never shown to new users. Back up `backend/data/wardrobe.db` before upgrading. The local development database was backed up to `backend/data/wardrobe.pre-auth-20261003.db` before migration. Legacy Cloudinary assets are not deleted; clean them up manually only after confirming they are not needed.

Passwords are stored as Argon2id hashes. Session tokens are random, stored hashed in the database, and issued only as HttpOnly cookies. A separate CSRF cookie/token pair protects authenticated writes. Keep the frontend and API on the same site where possible. For production, serve HTTPS, set `COOKIE_SECURE=true`, set `CORS_ORIGINS` to exact trusted origins, and use a shared persistent database. The built-in login/registration limiter is process-local and should be replaced by a shared store or gateway limiter when running multiple API workers/instances.

## Tests

Cloudinary network calls are mocked. Real credentials are not required.

```bash
pytest
```

## Deletion strategy

Deleting a clothing item removes the Cloudinary asset first, using its stored `public_id`, and deletes the database row only after Cloudinary returns `ok` or `not found`.

If Cloudinary fails, the database row stays so the wardrobe does not lose the record during a temporary outage and the delete can be retried. If the database delete fails after Cloudinary has already removed the file, the API logs the public id and returns an error. That order avoids leaving an orphaned Cloudinary asset when the network call fails.

`POST /api/uploads/discard` deletes an upload that was never saved as a clothing item, which the browser calls if saving metadata fails after a successful upload.

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/health` | API, database, and Cloudinary configuration status |
| `GET` | `/api/auth/csrf` | Issue/refresh CSRF token before login or registration |
| `POST` | `/api/auth/register` | Register `{name,email,password,confirm_password}`; signs user in |
| `POST` | `/api/auth/login` | Sign in with `{email,password}` |
| `POST` | `/api/auth/logout` | Revoke current session (CSRF required) |
| `GET` | `/api/auth/me` | Current safe user profile |
| `POST` | `/api/uploads/signature` | Authenticated, CSRF-protected signature for `wardrobeai/users/{id}/clothing` |
| `POST` | `/api/uploads/discard` | Delete an unsaved asset inside the current user's folder (CSRF required) |
| `GET` | `/api/items` | Authenticated paginated personal wardrobe. Query: `q`, `category`, `colour`, `pattern`, `style`, `occasion`, `sort`, `page`, `page_size` |
| `POST` | `/api/items` | Verify the current user's Cloudinary asset and save it (CSRF required) |
| `GET` | `/api/items/{item_id}` | One owned clothing item |
| `PUT` | `/api/items/{item_id}` | Update an owned item (CSRF required) |
| `DELETE` | `/api/items/{item_id}` | Delete an owned Cloudinary asset and row (CSRF required) |
| `GET` | `/api/stats` | Current user's counts, top category, recent items, and colours |
| `POST` | `/api/ai/recognize-clothing` | Recognize an owned persisted clothing asset |
| `POST` | `/api/ai/recommend-outfits` | Recommendations from current user's items only |
| `GET` | `/api/ai/capabilities` | Authenticated Cloudinary feature status |

Errors use `{ "error": { "code", "message", "fields"? } }`.
