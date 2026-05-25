# LinguaFlex Backend Service

This repository houses the Django and FastAPI backend for **LinguaFlex (Parlezhub)**. It manages user and teacher accounts, class scheduling, astrological readings/insights, blog publishing, real-time multi-file chat, and Stripe payments.

## Features

- **Modern Architecture**: Hybrid Django 6.x (REST API) + FastAPI (Real-time and WebSockets) backend.
- **Supabase Integration**: PostgreSQL database, JWT authentication, and secure bucket storage.
- **Astrology Engine**: Full natal charts, 16 divisional charts parsing, and dynamic custom-date transit caching.
- **AI Capabilities**: Deep integration with Google Gemini API for personalized astrological readings.
- **Payment Processing**: Stripe checkout, bulk payment methods management, and partial/full refund requests.
- **Bookings & Availability**: Weekly bulk availability slots, reschedule logic, approvals, and Zoom video meetings integration.
- **Unified Real-time Chat**: Unified HTTP POST endpoint for message sending (supporting optional multi-file attachments up to 10 files with magic-byte verification) + WebSocket push broadcasts.

---

## Project Structure

*   `accounts/`: Manages user, teacher/consultant profiles, gigs, and database messages.
*   `astrology/`: Astro-calculations, Natal & custom-date Transit caching, and AI insights.
*   `blogs/`: Teacher and Admin blog authorship, publishing, and file management.
*   `bookings/`: Booking schedules, bulk availability, cancellations, and Zoom meetings.
*   `chat/`: FastAPI real-time chat package (main setup, routers, dependencies, and services).
*   `core/`: Core helpers, Supabase clients, and asymmetric JWKS-based JWT token authentications.
*   `stripe_payments/`: Stripe payments, payment methods setup, and refund handling.
*   `rag_app/`: Main project settings, middleware, and WSGI/ASGI configurations.

---

## Setup Instructions

Follow these steps to set up the project locally:

1. **Clone the repository**:
   ```bash
   git clone <repository_url>
   cd lingua-flex-backend
   ```

2. **Sync Virtual Environment & Dependencies**:
   This project uses `uv` for lightning-fast package management and locks:
   ```bash
   uv sync
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the root directory and copy the contents from `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Fill in all environment variables (Supabase URL, Secret keys, Stripe/Resend/Zoom/Astrology/Gemini API keys).

4. **Apply Database Schema Migrations**:
   ```bash
   uv run python manage.py migrate
   ```

5. **Start Servers**:
   See the **Running both servers** section below to run Django (port 8000) and FastAPI (port 8001) simultaneously.

---

## Environment Variables

The `.env` file must define the following variables:

```ini
# Supabase Database & API Settings
DATABASE_URL=postgresql://...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SECRET_KEY=sb_secret_...
SUPABASE_BLOG_IMAGE_BUCKET=blog-images
SUPABASE_USER_UPLOADS_BUCKET=user-uploads
CHAT_UPLOADS_BUCKET=chat-uploads

# Frontend App Integration Paths
BASE_URL=http://localhost:3000
BASE_URL_SIGNIN=http://localhost:3000/auth/sign-in
BASE_URL_RESET_PASSWORD=http://localhost:3000/auth/reset-password

# Zoom API Credentials (Consultant Meetings)
ZOOM_ACCOUNT_ID=...
ZOOM_CLIENT_ID=...
ZOOM_CLIENT_SECRET=...
ZOOM_HOST_EMAIL=...

# Email Notification Service
RESEND_API_KEY=re_...

# Payment Processing (Stripe Integration)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Astrology Engine & AI Models
ASTROLOGY_API_KEY=ask_...
GEMINI_API_KEY=AIzaSy...

# Cryptographic Fields Encryption
FIELD_ENCRYPTION_KEY=...

# CORS & Trusted Origins
ALLOWED_HOSTS=api.shaktiwheel.in,localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,...
CSRF_TRUSTED_ORIGINS=https://app.parlezhub.com,...
```

---

## Authentication

Authentication is handled locally by verifying Supabase's asymmetric JWKS keys. Access and refresh token validation are securely done in the `core.authentication` module for REST API routes, and in `chat.dependencies` for WebSocket connections, eliminating external API network calls.

---

## Primary Dependencies

- **Django 6.x** & **Django REST Framework**
- **FastAPI** & **Uvicorn**
- **Supabase-py** & **Postgrest-py**
- **PyJWT** & **Cryptography**
- **Resend** (Email notifications)
- **Stripe** (Secure Checkout & Refunds)
- **python-multipart** (Form data file uploads)

---

## Running both servers (Django + FastAPI)

This project uses Django for the primary REST API and a modular FastAPI package (`chat/` booted via `fastapi_chat.py`) for realtime chat, unified multi-file sharing, and notifications. You can run both locally during development on different ports.

Recommended ports:

- Django: 8000
- FastAPI (uvicorn): 8001

### Local Setup with `uv` (Recommended)

1. **Install dependencies and sync environment**:
   This project uses `uv` for modern, high-performance package management.
   ```bash
   uv sync
   ```

2. **Configure environment variables**:
   Ensure required environment variables are set in a `.env` file (the project loads variables using `python-dotenv`). At minimum, verify Supabase DB credentials and keys (see the Environment Variables section above).

3. **Apply migrations**:
   ```bash
   uv run python manage.py migrate
   ```

4. **Start Django (port 8000)**:
   ```bash
   # In Terminal A
   uv run python manage.py runserver 0.0.0.0:8000
   ```

5. **Start FastAPI with uvicorn (port 8001)**:
   ```bash
   # In Terminal B
   uv run uvicorn fastapi_chat:app --host 0.0.0.0 --port 8001 --reload
   ```

6. **Verify**:

   - Django: http://127.0.0.1:8000/ and admin at `/django-admin/` or `/admin/`.
   - FastAPI Docs (Swagger): http://127.0.0.1:8001/docs or http://127.0.0.1:8001/redoc

### Notes and Troubleshooting:

- **Separate Terminals**: Use separate terminal windows or panes for each server to watch real-time request logs.
- **Security & JWT Verification**: FastAPI's token decoding is highly secure and fully verified locally using Supabase JWKS (asymmetric keys) with no network overhead.
- **WebSocket Handshakes**: WebSocket connections use the deferred accept model. The handshake succeeds immediately to prevent cross-origin/pre-handshake failures, and JWT validation is done asynchronously immediately after connection.
- **Production Setup**: For production, run Django and FastAPI behind a reverse proxy (such as nginx) and use gunicorn/uvicorn workers instead of `runserver`/`--reload`.

---

## Production Deployment (VPS with uv)

This project has been migrated to use `uv` for faster dependency management in production. When you pull the latest changes, use the following steps to deploy them to your VPS:

1. **Pull the latest code from the repository:**
   ```bash
   git pull origin main
   ```

2. **Sync the dependencies:**
   This command ensures your `.venv` environment exactly matches the `uv.lock` file:
   ```bash
   uv sync
   ```

3. **Apply database migrations:**
   Run migrations inside the `uv` environment:
   ```bash
   uv run python manage.py migrate
   ```

4. **Collect static files:**
   Gather all new static assets:
   ```bash
   uv run python manage.py collectstatic --noinput
   ```

5. **Restart the systemd services:**
   Restart both the Django backend (Gunicorn) and the FastAPI services to apply the code changes:
   ```bash
   sudo systemctl restart gunicorn
   sudo systemctl restart fastapi-chat
   ```

6. **Check Service Status:**
   To verify that everything is running correctly:
   ```bash
   sudo systemctl status gunicorn
   sudo systemctl status fastapi-chat
   ```

7. **View Logs:**
   If something goes wrong, you can check the logs:
   ```bash
   # Django/Gunicorn logs
   sudo journalctl -u gunicorn -f

   # FastAPI logs
   sudo journalctl -u fastapi-chat -f
   ```
