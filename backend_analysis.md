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

---

## 🔴 HIGH PRIORITY — Fix Immediately


### #H2 — `User.id` is `CharField` Instead of `UUIDField`
**File:** `core/models.py` line 99

`CharField(max_length=255)` wastes storage, allows any string as a PK, and indexes less efficiently than PostgreSQL's native UUID type.

```python
# ✅ Fix
id = models.UUIDField(primary_key=True, editable=False)
```
> Requires a careful migration with `USING id::uuid`. Test on staging first.

---

### #H3 — `Message.chat_id` Naming Violation — Creates `chat_id_id` DB Column
**File:** `accounts/models.py` line 63

`chat_id = models.ForeignKey(Chat, ...)` causes Django to internally create a DB column named `chat_id_id` (masked by `db_column="chat_id"`). `message.chat_id` returns the `Chat` *object*, not an ID — deeply confusing.

```python
# ✅ Fix
chat = models.ForeignKey(Chat, related_name="messages", ..., db_column="chat_id")
```

---



### #H6 — Astrology — `threading.Thread` Causes Silent Data Loss in Production
**File:** `astrology/views.py` lines 319–322, 347–350

Unmanaged threads are killed when Gunicorn recycles workers → insights silently never written to DB.

**Fix:** Replace with Celery: `generate_all_insights_async.delay(profile.id)`

---

### #H7 — Astrology — `time.sleep(1)` Polling Loop Blocks Workers (DoS Risk)
**File:** `astrology/views.py` lines 631–650

Holds a Django worker for up to 30 seconds per request. 10 concurrent users = all workers blocked.

**Fix:** Return `HTTP 202 Accepted` immediately. Client polls a `/insights/status/{task_id}/` endpoint.

---



## 🟡 MEDIUM PRIORITY

### #M1 — Hardcoded IP in `CORS_ALLOWED_ORIGINS`
**File:** `rag_app/settings.py` line 80

`"http://192.168.10.9:3000"` is a hardcoded dev machine IP. Should be loaded from an env variable like `CORS_EXTRA_ORIGINS`.

---

### #M2 — `Payment.gig` CASCADE Delete Destroys Financial History
**File:** `stripe_payments/models.py` line 30

If a `Gig` is deleted, the `Payment` record cascades and is deleted — destroying billing history.

**Fix:** Change to `on_delete=models.SET_NULL, null=True` and snapshot gig metadata into `Payment.metadata`.

---

### #M3 — `blogs/views.py` — Synchronous View Tracking on Every GET (DoS Risk)
Every public blog GET triggers synchronous DB writes (`get_or_create` + `update`). A write bottleneck and DoS vector.

**Fix:** Rate-limit with `django-ratelimit` short-term. Move analytics to Celery long-term.

---

### #M4 — `core/encryption.py` — Silent Plaintext Fallback in Production
If `FIELD_ENCRYPTION_KEY` is missing, `encrypt_value()` silently returns plaintext with only a log warning.

**Fix:**
```python
if not settings.DEBUG and not settings.FIELD_ENCRYPTION_KEY:
    raise ImproperlyConfigured("FIELD_ENCRYPTION_KEY must be set in production.")
```

---

## 🔵 NEW Issues (Introduced by Recent Refactoring)



### #N4 — `fastapi_chat.py` — Standalone Chat Service (Intentional, but Tightly Coupled)
This file is intentionally run as a **separate process** for the real-time chat feature. Architecturally fine.

**However:** It imports `accounts.models` and `core.models` directly via the Django ORM. If Django models change, the FastAPI service breaks silently.

**Fix:** The FastAPI service should communicate with Django via an internal REST API or shared database schema queries — not direct Django model imports.

---

## Priority Order for Fixes

| Priority | ID | Description |
|---|---|---|
| 🟡 1 | H6 | Unsafe threading in astrology |
| 🟡 2 | H7 | Synchronous polling loop DoS risk |
| 🟡 3 | M2 | Payment cascade delete risk |
| 🟡 4 | M3 | Blog view tracking DoS risk |
| 🟡 5 | M4 | Silent plaintext encryption fallback |
| ⬜ 6 | H2 | `User.id` CharField → UUIDField (requires staging migration) |
| ⬜ 7 | H3 | `Message.chat_id` naming violation |
| ⬜ 8 | M1 | Hardcoded IP in CORS settings |
| ⬜ 9 | N4 | FastAPI chat service ORM coupling |
