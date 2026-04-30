# Architectural Flaws and Issues Analysis

This document details the critical flaws, architectural issues, and technical debt found during the deep analysis of the `core`, `accounts`, and `rag_app` directories.

## 1. Massive Data Model Duplication (`core` vs `accounts`)
The most significant issue in the codebase is the split and duplication of core domain models across two different apps (`core` and `accounts`). This leads to a fragmented, confusing, and unmaintainable database schema.

*   **Teacher Profiles**:
    *   `core.Teacher` stores bio, teaching experience, languages, and hourly rate.
    *   `accounts.TeacherProfile` stores qualifications, experience, certificates, and an 'about' section.
    *   *Issue*: The system maintains two separate profiles for the same entity. The `core.User` model tries to keep these in sync using hacky methods like `create_teacher_profile()` which explicitly creates records in both tables simultaneously.
*   **Student/User Profiles**: 
    *   `core.Student` stores learning goals, proficiency, and target languages.
    *   `accounts.UserProfile` acts as the base profile for all users, storing bio, location, and languages.
    *   *Issue*: A user's identity and preferences are split across multiple overlapping tables, requiring multiple joins to get a complete picture of a user.
*   **Gigs/Services**:
    *   `core.TeacherGig` defines a service a teacher offers.
    *   `accounts.Gig` defines the exact same concept with slightly different fields.
    *   *Issue*: Total redundancy. Developers will constantly be confused about which model is the "source of truth".
*   **AI Conversations**:
    *   `core.AIConversation` and `accounts.VoiceConversation` appear to serve the exact same purpose (storing transcripts and AI feedback from voice interactions).


## 3. Authentication Logic Coupling (`core/views.py`)
*   **Registration Sprawl**: The logic for registering a user is duplicated. `core.views.RegisterView` handles basic signup, while `accounts.views.RegisterWithProfileView` duplicates the exact same Supabase signup logic but adds profile creation on top of it.
*   **Tight App Coupling**: `GoogleOAuthCallbackView` inside `core` directly imports and manipulates `accounts.UserProfile` and `accounts.TeacherProfile`. This creates a tight coupling where the `core` auth system is hardcoded to understand the schema of the `accounts` app, violating separation of concerns.

## 4. Dangerous Global Initializations (`core/views.py`)
*   **Module-Level Zoom Client**: In `core/views.py`, the `ZoomClient` is initialized at the module level in a global `try/except` block. 
*   **The Flaw**: If the server starts without the correct environment variables, it silently prints a warning and disables Zoom functionality for the entire lifespan of the worker process. It also runs this initialization every time the file is imported. This should be initialized lazily (inside a function or class property) or managed via a singleton service.

## 5. Profile Management Hacks (`core/models.py`)
*   **Exception-Driven Control Flow**: The `User` model uses methods like `has_teacher()` and `has_student()` which wrap `try/except` blocks around reverse relation lookups (e.g., `user.teacher`). Using exceptions for standard control flow (checking if a related object exists) is a performance anti-pattern. Django provides `hasattr()` or `User.objects.filter(teacher__isnull=False)` for this exact purpose.

## 6. Configuration and Environment Issues (`rag_app/settings.py`)
*   **Hardcoded Environments**: `DEBUG = True` is hardcoded. There is no logic to toggle this off in production based on environment variables.
*   **Hardcoded Origins**: `CORS_ALLOWED_ORIGINS` contains hardcoded local IP addresses (e.g., `http://192.168.10.9:3000`). This should be dynamically loaded via an environment variable to prevent security leaks and deployment issues.
*   **Database Lock-in**: The `DATABASES` setting relies entirely on Supabase environment variables. The standard `dj_database_url` is commented out, making it unnecessarily difficult for new developers to spin up a local SQLite database for quick testing.

## 7. Extended Model Redundancy (`bookings` & `stripe_payments`)
The model duplication problem extends beyond user profiles into the core business logic of bookings and payments.
*   **Sessions**: The `core` app defines a `Session` model. Meanwhile, the `bookings` app introduces a completely separate `SessionBooking` model. Both represent the exact same concept (a meeting between a student and teacher).
*   **Payments**: The `core` app defines a `SessionBilling` model. The `stripe_payments` app introduces a `Payment` model. This creates parallel billing tracking systems.
*   **Tangled Dependencies**: The `Payment` model in `stripe_payments` has Foreign Keys pointing to `bookings.SessionBooking`, `core.User`, and `accounts.Gig`. This tightly couples the payments module to three different apps, making it nearly impossible to test or modify in isolation.

## 8. Synchronous Analytics and Unsafe Database Writes (`blogs`)
*   **Synchronous View Tracking**: In `blogs.views.PublicBlogDetailView`, every single `GET` request triggers a synchronous database write to `BlogView` to track the viewer's IP address, followed by an `update()` call to increment the `view_count` on the `Blog` model. 
*   **The Flaw**: Performing relational database inserts on every read request is a massive performance bottleneck and a vector for Denial of Service (DoS) attacks. Analytics tracking should be handled asynchronously (e.g., via Celery, Redis, or an external analytics service).

## 9. Non-Atomic Third-Party Integrations (`bookings`)
*   **Zoom Silent Failures**: In `bookings.views.SessionBookingViewSet.create()`, if a video call session is booked but the Zoom API fails to generate a meeting link, the booking is still saved to the database. The API returns a `201 Created` status with a warning tucked into the JSON payload.
*   **The Flaw**: This breaks atomicity. A "video call" booking without a video link is in an invalid state. The transaction should be rolled back entirely if the essential third-party resource fails to generate, returning a `400` or `502` error to the client instead of a partial success.

## 10. Concurrency and Scalability Issues (`astrology`)
*   **Unsafe Threading**: In `astrology/views.py`, background tasks (like `generate_all_insights_async`) are launched using `threading.Thread(target=...).start()`. In a production WSGI/ASGI environment (like Gunicorn), worker processes can be killed or recycled at any time, instantly destroying these unmanaged threads and causing silent data loss. Background jobs must be managed by a message queue (e.g., Celery).
*   **Synchronous Polling**: Inside `AstrologyInsightView.get()`, the code uses a `time.sleep(1)` loop to wait for up to 30 seconds for background insights to finish generating. This ties up a Django worker thread completely. Under load, this will rapidly exhaust the worker pool, bringing the entire site down.

## 11. Heavy Token Usage and String Formatting (`astrology/services.py`)
*   **Massive AI Context Windows**: The `GeminiAIService` passes extremely large, raw JSON dumps (like the full `kp_system` or `ashtakvarga` API responses) directly into the string prompt via `json.dumps()`. This consumes massive amounts of tokens, degrades AI performance/focus, and increases costs. The data should be parsed and reduced to only the strictly necessary astrological data points before being sent to the LLM.

## 12. Inefficient Cache Invalidation (`astrology/views.py`)
*   **On-Demand Expiration**: The `TransitView` and `NakshatraPredictionView` invalidate their caches "on the fly" by checking if the user's local date differs from the cached date. While functional, it means the first request of the day for any user will experience a 3-5 second delay as it synchronously calls the external API. This should be converted into a nightly cron job that pre-warms the cache for active users.

## 13. Model Architecture Deep-Dive: `core/models.py` vs `accounts/models.py`

### 13.1 Split Teacher Profile (The #1 Problem)

The single most damaging issue: a "teacher" has **two separate, disconnected model rows** in the database.

| Field | `core.Teacher` | `accounts.TeacherProfile` |
|---|---|---|
| Link | `user` (OneToOne → User) | `user_profile` (OneToOne → UserProfile) |
| Bio/About | `bio` | `about` |
| Experience | `teaching_experience` (int, years) | `experience_years` (PositiveInt) |
| Languages | `teaching_languages` (JSON) | — |
| Hourly Rate | `hourly_rate` (Decimal) | — |
| Certs | via `TeacherCertificate` model | `certificates` (JSON field) |
| Qualifications | — | `qualification` (TextField) |

**Result**: The `create_teacher_profile()` method on `User` must create two rows simultaneously and keep them in sync forever. Any update to one must be manually mirrored to the other. This is a data integrity time bomb.

### 13.2 Duplicate Gigs Models

`core.TeacherGig` and `accounts.Gig` represent the exact same concept — a service a teacher offers — but with different field sets and different ForeignKey targets:

- `core.TeacherGig.teacher` → `core.Teacher`
- `accounts.Gig.teacher` → `accounts.TeacherProfile`

The `accounts.Gig` model is more complete (has `category`, `status`, `tags`, `short_description`). `core.TeacherGig` is a stub that should be deleted and replaced entirely.

### 13.3 Split AI/Voice Conversation Models

`core.AIConversation` and `accounts.VoiceConversation` both store AI conversation transcripts, but with different schemas:

- `core.AIConversation`: links to `core.Student`, stores `prompt`/`response` as flat text
- `accounts.VoiceConversation`: links directly to `User`, stores `transcription` as structured JSON

**Result**: There is no canonical place to look up a user's conversation history. Both models exist in the DB simultaneously.

### 13.4 Exception-Driven Control Flow (Performance Anti-Pattern)

In `core.User.has_teacher()` and `has_student()`, existence checks work by catching exceptions:

```python
# ❌ Bad — raises and catches a DoesNotExist exception on every miss
try:
    if hasattr(self, 'teacher') and self.teacher is not None:
        return True
except Exception:
    pass
```

`hasattr(self, 'teacher')` will attempt to access the reverse relation, which **hits the database AND raises `RelatedObjectDoesNotExist`** if the object doesn't exist. The correct approach:

```python
# ✅ Correct — no exception, no extra query if prefetched
return Teacher.objects.filter(user=self).exists()
```

### 13.5 `User.id` is `CharField(max_length=255)` — Should be `UUIDField`

The `User` model uses `id = models.CharField(primary_key=True, max_length=255)` to store Supabase UUIDs. Since Supabase always provides standard UUIDs, this should be:

```python
# ✅ Correct
id = models.UUIDField(primary_key=True, editable=False)
```

**Why**: Django's `UUIDField` validates UUID format, stores as native UUID type in PostgreSQL (not as a long varchar), and indexes more efficiently. `CharField(max_length=255)` wastes storage and allows any string to be stored as an ID.

### 13.6 `File.file` Uses `FileField(upload_to="uploads/")` — Dead Code

`core.File.file = models.FileField(upload_to="uploads/")` points to Django's local media storage. But the codebase uses Supabase Storage for all file uploads. The `file` field would write to the local filesystem, conflicting with the `storage_key` field on the same model. One of these must be removed.

### 13.7 `Message.chat_id` Naming Convention Violation

The field is named `chat_id` but it's a ForeignKey, not an integer ID:

```python
# ❌ Confusing — DRF will serialize this as "chat_id_id"
chat_id = models.ForeignKey(Chat, ...)

# ✅ Correct Django convention
chat = models.ForeignKey(Chat, ...)
```

Django's ORM automatically appends `_id` to FK column names. Naming the field `chat_id` means the actual database column will be `chat_id_id`, and the Python attribute `message.chat_id` returns the Chat object (not an integer), which is counterintuitive.
