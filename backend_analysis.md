# Backend Architecture Analysis — LinguaFlex
_Last Updated: 2026-05-04_

---

## ✅ RESOLVED Issues

### ~~#1 — Split Teacher Profile (core.Teacher + accounts.TeacherProfile)~~
**RESOLVED.** `core.Teacher` fully deleted (`core/migrations/0006_delete_teacher.py`). All fields (`teaching_languages`, `hourly_rate`, `is_verified`) migrated into `accounts.TeacherProfile`.

### ~~#2 — Student Model Duplication (core.Student + accounts.UserProfile)~~
**RESOLVED.** `core.Student` deleted. `accounts.UserProfile` is the single source of truth.

### ~~#3 — Duplicate Gigs Models (core.TeacherGig + accounts.Gig)~~
**RESOLVED.** `core.TeacherGig` deleted. `accounts.Gig` is canonical.

### ~~#4 — AIConversation Duplication~~
**RESOLVED.** `core.AIConversation` deleted. `accounts.VoiceConversation` is canonical.

### ~~#5 — Dead Zoom Code at Module Level (core/views.py)~~
**RESOLVED.** Module-level `ZoomClient` initialization block removed.

### ~~#6 — Configuration: DEBUG hardcoded~~
**RESOLVED.** `DEBUG = os.getenv("DEBUG", "True") == "True"` — now env-controlled.

### ~~#7 — File.file Dead Code~~
**RESOLVED.** `core.File` model deleted.

### ~~#8 — Duplicate Sessions/Billing Models~~
**RESOLVED.** `core.Session` and `core.SessionBilling` deleted. `bookings.SessionBooking` and `stripe_payments.Payment` are canonical.

### ~~#9 — Broken `weekly_availability` Lookup (H5)~~
**RESOLVED.** Fixed the reverse relation lookup in `bookings/views.py` to use `user_profile__user_id` instead of `user_id`.

### ~~#10 — `select_related("category")` Crash in Blogs (H9)~~
**RESOLVED.** Removed all stale `.select_related("category")` calls and related filtering logic from `blogs/views.py`.

### ~~#11 — Orphaned RegisterView (H10)~~
**RESOLVED.** Fully deleted the duplicate `RegisterView` and its associated `UserRegistrationSerializer` from the `core` app.

### ~~#12 — Bookings Role Checks Block BOTH Role (N2)~~
**RESOLVED.** Updated all 6 teacher-only booking endpoints to correctly authorize users with the `BOTH` role.

### ~~#13 — Signals Missing BOTH Role (N3)~~
**RESOLVED.** Updated `accounts/signals.py` to automatically create a `TeacherProfile` when a user registers with the `BOTH` role.

### ~~#14 — Astrology Delegation Excludes BOTH Role (N1)~~
**RESOLVED.** Updated the `_resolve_profile` access check in `astrology/views.py` to allow the `BOTH` role to view delegated dashboards.

### ~~#16 — UserProfile.role Duplication (H4)~~
**RESOLVED.** Completely removed the redundant `role` field from `accounts.UserProfile`, updated all views to rely solely on `User.role`, and removed references in the admin panel and serializers. A migration has been generated.

### ~~#17 — Non-Atomic Zoom Failure (H8)~~
**RESOLVED.** Updated the `bookings/views.py` `create` method to explicitly set `transaction.set_rollback(True)` and return an `HTTP 502 Bad Gateway` if the Zoom API call fails, preventing corrupted video bookings from being saved.

### ~~#18 — Astrology Polling Loop Blocks Workers (H7)~~
**RESOLVED.** Replaced the 30-second `time.sleep(1)` worker-blocking polling loop in `astrology/views.py` with an immediate `HTTP 202 Accepted` response. The frontend is expected to poll back after a short delay.

### ~~#19 — Gemini Rate Limit via Fixed Sleep (H6 partial)~~
**RESOLVED (rate-limit strategy).** Replaced the fixed `time.sleep(4.5)` between every Gemini call in `astrology/tasks.py` with an exponential backoff retry helper (`_generate_insight_with_backoff`). Calls now proceed at full speed and only back off (5s → 10s → 20s → 40s) when a `429 / resource_exhausted` error is actually received. The background thread execution model is retained (Celery migration deferred to future infrastructure work).

### ~~#20 — Payment Cascade Delete Risk (M2)~~
**RESOLVED.** Changed `Payment.gig` from `CASCADE` to `SET_NULL` in `stripe_payments/models.py`. This ensures that deleting a Gig will no longer destroy the associated financial history.

### ~~#21 — Blog View Tracking DoS Risk (M3)~~
**RESOLVED (Feature Removed).** Per user request, the entire blog view tracking system—including the `BlogView` model, the `view_count` field on the `Blog` model, and all associated logic/admin panels—has been removed from the codebase. This completely eliminates the DoS risk associated with synchronous view tracking.

### ~~#22 — Silent Plaintext Encryption Fallback (M4)~~
**RESOLVED.** Updated `core/encryption.py` to raise a hard `ImproperlyConfigured` exception in production (when `DEBUG=False`) if the `FIELD_ENCRYPTION_KEY` is missing. This prevents sensitive data from being accidentally saved in plaintext.

### ~~#23 — Message.chat_id Naming Violation (H3)~~
**RESOLVED.** Renamed `chat_id` and `sender_id` to `chat` and `sender` in the `Message` model and associated serializers/views. Used `db_column` to preserve the existing database schema while fixing the Django-level naming confusion.

### ~~#24 — Hardcoded IP in CORS_ALLOWED_ORIGINS (M1)~~
**RESOLVED.** Removed the hardcoded `192.168.10.9:3000` IP from `rag_app/settings.py` and implemented support for a `CORS_EXTRA_ORIGINS` environment variable to securely handle varying local dev environments.

### ~~#25 — FastAPI Chat Service ORM Coupling (N4)~~
**RESOLVED.** Refactored `fastapi_chat.py` to remove direct Django ORM imports (`core.models.User`, `accounts.models.UserProfile`). The standalone chat service now uses the Supabase client (`get_admin_client()`) to fetch user data directly from the shared database schema, decoupling it from Django model changes.

### ~~#26 — User.id CharField → UUIDField (H2)~~
**RESOLVED.** Successfully reset the migrations and converted `User.id` to a native `UUIDField`. This improves storage efficiency and indexing performance in PostgreSQL. All foreign keys referencing the user model are now also using UUIDs.

---

## 🔴 HIGH PRIORITY — Fix Immediately










## 🔵 NEW Issues (Introduced by Recent Refactoring)

