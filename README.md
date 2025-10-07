# Backend Supabase Project

This project is a Django-based backend application integrated with Supabase and OpenAI APIs. It supports authentication with Supabase tokens and provides RESTful APIs.

## Features

- Django 5.2.4 backend
- PostgreSQL database on Supabase
- Custom authentication with Supabase tokens
- REST API with Django REST Framework
- OpenAI integration support
- Configuration through environment variables

## Project Structure

- `core/`: Main application logic including models, views, serializers, and authentication
- `rag_app/`: Django project settings and configurations
- `manage.py`: Django CLI utility
- `requirements.txt`: Python dependencies

## Setup Instructions

Follow these detailed steps to set up the project locally:

1. **Clone the repository**

   - Open a terminal or command prompt.
   - Run `git clone <repository_url>` replacing `<repository_url>` with your repository's URL.
   - Navigate into the cloned directory: `cd backend_supabase`.

2. **Set up a Python virtual environment**

   - Create a virtual environment by running:
     - On Windows: `python -m venv venv`
     - On macOS/Linux: `python3 -m venv venv`
   - Activate the virtual environment:
     - On Windows (PowerShell): `venv\Scripts\Activate.ps1`
     - On Windows (cmd): `venv\Scripts\activate.bat`
     - On macOS/Linux: `source venv/bin/activate`

3. **Install required dependencies**

   - With the virtual environment activated, run:
     ```
     pip install -r requirements.txt
     ```

4. **Configure environment variables**

   - Create a `.env` file in the project root directory.
   - Define all required environment variables as listed in the Environment Variables section.

5. **Apply database migrations**

   - Run the following command to setup the database schema:
     ```
     python manage.py migrate
     ```

6. **Run the development server**

   - Start the Django development server with:
     ```
     python manage.py runserver
     ```
   - The server should start at `http://127.0.0.1:8000/` by default.

7. **(Optional) Create a superuser**
   - To access Django admin, create a superuser:
     ```
     python manage.py createsuperuser
     ```

These steps ensure you have a working local development environment for the backend Supabase project.

## API Endpoints

### User Management

- `POST /api/register/`: Register a new user.
- `POST /api/login/`: Authenticate a user and obtain a token.
- `POST /api/password-reset/`: Initiate password reset process.
- `POST /api/password-reset/confirm/`: Confirm password reset with token.
- `POST /api/token/refresh/`: Refresh JWT authentication token.
- `GET /api/user/profile/`: Retrieve user profile information.
- `POST /api/user/profile-picture/`: Upload or update user profile picture.
- `GET /api/user/profile-picture-url/`: Get URL of the user's profile picture.

### File Management

- `GET /api/user-files/`: List files belonging to the authenticated user.
- `POST /api/files/upload/`: Upload a new file.
- `DELETE /api/user-files/<file_name>/`: Delete a specific file by its name.

## Environment Variables

The `.env` file should contain the following variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_key
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_DB_URL=your_database_url
SUPABASE_DBNAME=your_db_name
SUPABASE_USER=your_db_username
SUPABASE_PASSWORD=your_db_password
SUPABASE_HOST=your_db_host
SUPABASE_PORT=your_db_port
BASE_URL_RESET_PASSWORD=url_for_password_reset
BASE_URL_SIGNIN=url_for_signin
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

## Authentication

- Custom Supabase token authentication is implemented in the `core.authentication` module.
- JWT tokens configured for access and refresh with custom authentication backend.

## Dependencies

- Django
- Django REST Framework
- djangorestframework-simplejwt
- dj-database-url
- python-dotenv
- corsheaders

## License

Specify your project license here.

---

## Running both servers (Django + FastAPI)

This project uses Django for the primary REST API and a small FastAPI app (`fastapi_chat.py`) for realtime chat and notifications. You can run both locally during development on different ports.

Recommended ports:

- Django: 8000
- FastAPI (uvicorn): 8001

PowerShell example (from project root):

1. Activate virtual environment and install dependencies (if not already done):

```powershell
# Activate venv (PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

2. Ensure required environment variables are set in a `.env` file (project loads with python-dotenv). At minimum verify Supabase DB and keys (see Environment Variables above).

3. Apply migrations and create a superuser if needed:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

4. Start Django (port 8000):

```powershell
# In Terminal A
python manage.py runserver 0.0.0.0:8000
```

5. Start FastAPI with uvicorn (port 8001):

```powershell
# In Terminal B
python -m uvicorn fastapi_chat:app --host 0.0.0.0 --port 8001 --reload
```

6. Verify

- Django: http://127.0.0.1:8000/ and admin at `/django-admin/` or `/admin/`.
- FastAPI: http://127.0.0.1:8001/docs (Swagger) or http://127.0.0.1:8001/redoc

Notes and troubleshooting:

- Use separate terminals for each server so you can watch logs.
- If `uvicorn` isn't available, use `python -m uvicorn ...` as shown above.
- Ensure `SUPABASE_SERVICE_ROLE_KEY` and other server-only secrets are only used on the server and never exposed to client code.
- FastAPI's token decoding in `fastapi_chat.py` currently skips signature verification; do not use that in production. Prefer verifying JWTs with Supabase JWKs or via Supabase API.
- For production, run Django and FastAPI behind a reverse proxy (nginx) and use gunicorn/uvicorn workers instead of `runserver`/`--reload`.
