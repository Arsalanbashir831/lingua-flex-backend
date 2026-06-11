# ParlezHub Backend — Full Architecture

> **Stack**: Django 5.2 · DRF · PostgreSQL (Supabase) · Gemini AI · Stripe · Zoom API · FastAPI (chat)  
> **Auth**: Supabase JWT (JWKS asymmetric verification, no password stored in Django)  
> **Docs**: Auto-generated OpenAPI at `/docs/` via `drf-spectacular`

---

## High-Level Overview

```mermaid
graph TB
    Client["Frontend Client\n(Next.js / Mobile)"]

    subgraph Django["Django Monolith — rag_app"]
        direction TB
        MW["Middleware Stack\nCORS · CSRF · Auth"]
        Router["URL Router\nrag_app/urls.py"]

        subgraph Apps["Django Apps"]
            CORE["🔐 core\nUser model · Auth · Supabase client"]
            ACCOUNTS["👤 accounts\nProfiles · Gigs · Chat · Voice"]
            BOOKINGS["📅 bookings\nSessions · Availability · Zoom"]
            PAYMENTS["💳 stripe_payments\nPayments · Refunds · Analytics"]
            ASTROLOGY["🔮 astrology\nBirth charts · AI insights · Festival calendar"]
            BLOGS["📝 blogs\nTeacher articles"]
            FAMILY["🌳 family_tree\nMembers · Relationships"]
        end
    end

    subgraph External["External Services"]
        SUPABASE["Supabase\nAuth JWT + PostgreSQL + Storage"]
        GEMINI["Google Gemini AI\nAstrological insight generation"]
        ASTRO_API["astrology-api.io\nVedic chart calculation"]
        STRIPE["Stripe\nPayments · Webhooks"]
        ZOOM["Zoom\nServer-to-Server OAuth · Meetings"]
        RESEND["Resend\nTransactional email"]
    end

    Client -->|Bearer JWT| MW
    MW --> Router
    Router --> Apps
    CORE --> SUPABASE
    ASTROLOGY --> GEMINI
    ASTROLOGY --> ASTRO_API
    PAYMENTS --> STRIPE
    BOOKINGS --> ZOOM
    ACCOUNTS --> RESEND
```

---

## Authentication Pipeline

```mermaid
sequenceDiagram
    participant C as Client
    participant DJ as Django (DRF)
    participant SA as SupabaseTokenAuthentication
    participant JWK as Supabase JWKS
    participant DB as PostgreSQL

    C->>DJ: Request + Authorization: Bearer <JWT>
    DJ->>SA: authenticate(request)
    SA->>JWK: GET /auth/v1/.well-known/jwks.json (cached)
    JWK-->>SA: Public signing key (ES256/RS256)
    SA->>SA: jwt.decode() — verify signature + expiry
    SA->>DB: User.objects.get(id=payload["sub"])
    DB-->>SA: User instance
    SA-->>DJ: (user, None)
    DJ->>DJ: Execute view with request.user set
```

**Key points:**
- No passwords stored in Django — Supabase owns authentication
- JWKS client is a **module-level singleton** — key fetches are cached in-process
- User UUID in Django **matches** the Supabase `auth.users.id`
- Django admin login uses `ModelBackend` (separate path for superusers)

---

## Module-by-Module Breakdown

### 🔐 `core` — Foundation

| File | Responsibility |
|---|---|
| `models.py` | Custom `User` (AbstractBaseUser) with roles: `STUDENT`, `TEACHER`, `BOTH`, `ADMIN` |
| `authentication.py` | `SupabaseTokenAuthentication` — JWKS JWT verifier |
| `supabase_client.py` | Admin Supabase SDK client (server-side only) |
| `encryption.py` | Fernet-based field-level encryption helpers |
| `views.py` | Auth sync, Google OAuth, password reset, voice sessions |
| `urls.py` | `/api/` — auth/session endpoints |

**User model highlights:**
```
User
 ├── id          UUID (= Supabase sub)
 ├── email       unique
 ├── role        STUDENT | TEACHER | BOTH | ADMIN  (nullable)
 ├── auth_provider  EMAIL | GOOGLE
 ├── is_oauth_user
 └── email_verified
```

---

### 👤 `accounts` — Profiles, Gigs & Messaging

```mermaid
erDiagram
    User ||--o| UserProfile : "has profile"
    UserProfile ||--o| TeacherProfile : "can be teacher"
    TeacherProfile ||--o{ Gig : "posts gigs"
    Gig ||--o{ SessionBooking : "booked via"
    User ||--o{ Chat : "participant1 / participant2"
    Chat ||--o{ Message : "contains"
    Message ||--o{ MessageAttachment : "can have files"
    User ||--o{ VoiceConversation : "records"
```

| Model | Purpose |
|---|---|
| `UserProfile` | Bio, city, country, native/learning language |
| `TeacherProfile` | Qualification, experience, certificates, hourly rate, `is_verified` |
| `Gig` | Service listings (language / astrology / general) with price & duration |
| `Chat` + `Message` + `MessageAttachment` | P2P messaging with Supabase Storage file uploads |
| `VoiceConversation` | Stores OpenAI speech-to-speech session transcription + AI feedback |

**Key API routes** (`/api/accounts/`):
- `POST /sync-supabase/` — Creates Django user row from Supabase token
- `POST /set-role/` — Assigns STUDENT or TEACHER role (upgrades to BOTH)
- `GET /profiles/me/roles/` — Returns unified role status with self-healing
- `GET/PATCH /profiles/teacher/` — Teacher profile management
- `GET /teachers/` — Browse verified teachers
- `GET/POST /gigs/` — Teacher gig management

---

### 📅 `bookings` — Session Scheduling

```mermaid
erDiagram
    User ||--o{ TeacherAvailability : "sets availability"
    User ||--o{ SessionBooking : "student books"
    User ||--o{ SessionBooking : "teacher receives"
    Gig ||--o{ SessionBooking : "booked for gig"
    SessionBooking ||--o| Payment : "has payment"
```

| Model | Purpose |
|---|---|
| `TeacherAvailability` | Weekly recurring or one-off slots (day-of-week + time range) |
| `SessionBooking` | Full lifecycle: PENDING → CONFIRMED → COMPLETED/CANCELLED + reschedule workflow |

**Zoom integration** (`zoom_service.py`):
- Server-to-Server OAuth token (auto-refreshed)
- Creates a Zoom meeting on booking confirmation
- Stores `zoom_meeting_id`, `zoom_join_url`, `zoom_start_url`, `zoom_password`

**Booking statuses:** `PENDING → CONFIRMED → COMPLETED / CANCELLED`  
**Reschedule workflow:** Either party requests → other confirms/declines → history preserved

---

### 💳 `stripe_payments` — Payments

```mermaid
erDiagram
    SessionBooking ||--|| Payment : "1-to-1"
    Payment ||--o{ RefundRequest : "can have refunds"
    User ||--o| StripeCustomer : "linked stripe customer"
    User ||--o{ SavedPaymentMethod : "saved cards"
    PaymentAnalytics }|--|| date : "aggregated daily"
```

| Model | Purpose |
|---|---|
| `Payment` | Stripe PaymentIntent tracking, platform fee calculation (5%), status lifecycle |
| `SavedPaymentMethod` | Tokenized card display (brand, last 4) — never stores raw card data |
| `RefundRequest` | Student-initiated → admin review → Stripe refund |
| `StripeCustomer` | 1-to-1 link between `User` and `stripe.Customer` |
| `PaymentAnalytics` | Daily aggregated metrics for admin dashboard |

**Payment flow:**
1. Student creates `PaymentIntent` via `/api/payments/create-intent/`
2. Frontend confirms card with Stripe.js
3. Stripe sends webhook → Django updates `Payment.status`
4. `SessionBooking.payment_status` updated accordingly

---

### 🔮 `astrology` — Vedic Astrology Engine

This is the most complex module. It has several distinct layers:

```mermaid
graph TD
    subgraph Views["API Views (views.py ~1500 lines)"]
        BP[BirthProfileView]
        NC[NatalChartView]
        TR[TransitView]
        DA[DashaView]
        NK[NakshatraPredictionView]
        AI[AstrologyInsightView]
        CH[AstrologyInsightChatView]
        ACC[AstrologyAccessView]
        GU[GuestProfileListView]
        FC[FestivalCalendarView]
        TS[TeacherStudentDashboardsView]
    end

    subgraph Services["services.py"]
        API[AstrologyAPIClient]
        GEMINI_SVC[Gemini AI calls]
    end

    subgraph Analyzers["analyzers/ (27 files)"]
        BASE[base.py]
        GENERAL["General Readings\n(mental_health, marriage,\nmedical, foreign_travel...)"]
        DIVISIONAL["Divisional Charts\n(D2, D4, D7, D10, D12, D27, D60)"]
        REMEDIES["Remedies & Planets\n(benefic, malefic, darakaraka...)"]
    end

    subgraph Models["models.py"]
        BPROF[BirthProfile]
        NATAL[NatalChartCache]
        TRANSIT[TransitCache]
        NAKSH[NakshatraPredictionCache]
        INSIGHT[AstrologyInsight]
        CHAT[AstrologyChat]
        ACCESS[AstrologyDashboardAccess]
        FEST[FestivalCalendarCache]
        PROMPT[AIPromptConfiguration]
    end

    subgraph ExternalAPIs["External"]
        ASTRO_IO[astrology-api.io]
        GEMINI_AI[Google Gemini]
    end

    Views --> Services
    Views --> Models
    Services --> Analyzers
    Services --> ASTRO_IO
    Services --> GEMINI_AI
    Analyzers --> Models
```

**Data flow for an insight request:**

```mermaid
sequenceDiagram
    participant C as Client
    participant V as AstrologyInsightView
    participant DB as Database
    participant API as astrology-api.io
    participant AN as Analyzer (e.g. marriage.py)
    participant G as Gemini AI

    C->>V: GET /api/astrology/insights/marriage/
    V->>DB: Check AstrologyInsight cache (birth_profile, category)
    alt Cache HIT
        DB-->>V: Cached insight text
        V-->>C: Return cached response
    else Cache MISS
        V->>DB: Load NatalChartCache
        DB-->>V: birth_details + divisional + kp + dasha data
        V->>AN: build_marriage_prompt(natal_data, transit_data, ...)
        AN-->>V: Formatted prompt string
        V->>G: gemini.generate_content(prompt)
        G-->>V: AI-generated insight text
        V->>DB: Save to AstrologyInsight
        V-->>C: Return new insight
    end
```

**Caching strategy:**

| Cache Model | Key | TTL |
|---|---|---|
| `NatalChartCache` | `birth_profile` (1-to-1) | Forever (birth data never changes) |
| `TransitCache` | `(birth_profile, date)` | Per calendar day |
| `NakshatraPredictionCache` | `birth_profile` (1-to-1) | Expires at local midnight |
| `AstrologyInsight` | `(birth_profile, category)` | Forever unless invalidated |
| `FestivalCalendarCache` | `(year, festival_type, language, region)` | Forever (static yearly data) |

**Encryption:** Birth data fields (`birth_year`, `birth_month`, `city`, etc.) use Fernet symmetric encryption via `EncryptedCharField` / `EncryptedIntegerField`.

**Teacher–Student dashboard access:**

```mermaid
graph LR
    Student -->|grants access| AstrologyDashboardAccess
    AstrologyDashboardAccess -->|teacher can view| TeacherView[TeacherStudentDashboardsView]
    TeacherView -->|role check| RoleCheck{"role in\nTEACHER, BOTH?"}
    RoleCheck -->|Yes| StudentList["Return list of\ngranted students"]
    RoleCheck -->|No| Forbidden["403 Forbidden"]
```

**Analyzers breakdown** (`analyzers/`):

| File | Category |
|---|---|
| `base.py` | `BaseAnalyzer` ABC |
| `mental_health.py` | Mental health reading |
| `marriage.py` | Marriage timing analysis |
| `medical.py` | Medical astrology |
| `foreign_travel.py` | Foreign travel & settlement |
| `btr.py` | Birth time rectification |
| `darakaraka.py` | Spouse profile (Jaimini) |
| `d2_hora.py` | D2 Hora chart |
| `d4_chaturthamsha.py` | D4 Chaturthamsha chart |
| `d7_saptamsha.py` | D7 Saptamsha chart |
| `d10_dashamsha.py` | D10 Dashamsha chart |
| `d12_dwadashamsha.py` | D12 Dwadashamsha chart |
| `d27_saptavimshamsha.py` | D27 Saptavimshamsha chart |
| `d60_shashtiamsha.py` | D60 Shashtiamsha chart |
| `benefic_planets.py` | Benefic planet analysis |
| `malefic_planets.py` | Malefic planet analysis |
| `chart_analysis.py` | General chart analysis |
| `planetary_states.py` | Planetary avatars & states |
| `lagna_lord.py` | Lagna lord position |
| `rashi_planets.py` | Rashi planet meanings |
| `challenges.py` | Challenges & learning |
| `parasari.py` | Parasari relationships |
| `navatara.py` | Navatara (nine stars) |
| `prosperity_sav.py` | Prosperity & career (SAV) |
| `astro_energy.py` | 12-dimensional astro energy |
| `daily_tara.py` | Daily Tara Bala |
| `navatara.py` | Navatara logic |

---

### 📝 `blogs` — Teacher Content

```mermaid
erDiagram
    TeacherProfile ||--o{ Blog : "authors"
```

| Feature | Detail |
|---|---|
| Statuses | `DRAFT → PUBLISHED → ARCHIVED` |
| Auto-slug | Generated from title, deduplicated with counter |
| Read time | Auto-calculated (word count / 200 wpm) |
| Storage | Thumbnails stored via Supabase Storage bucket |
| SEO | `meta_description`, `slug`, `published_at` |

---

### 🌳 `family_tree` — Genealogy

```mermaid
erDiagram
    User ||--o{ FamilyMember : "owns"
    FamilyMember ||--o{ FamilyRelationship : "has (as profile)"
    FamilyMember ||--o{ FamilyRelationship : "has (as relative)"
    FamilyMember }o--o| User : "optionally linked to"
```

Simple graph structure:
- **`FamilyMember`** — a person in the tree (may optionally link to a registered `User`)
- **`FamilyRelationship`** — directed edge: `(profile) --[PARENT|SPOUSE]--> (relative)`
- Fully tested with 14 integration tests

---

## URL Map

| Prefix | Module | Key Endpoints |
|---|---|---|
| `/admin/` | Django Admin | Built-in admin panel |
| `/api/` | `core` | sync-supabase, set-role, google-oauth, password-reset, voice |
| `/api/accounts/` | `accounts` | profiles, teachers, gigs, chats, messages |
| `/api/bookings/` | `bookings` | sessions, availability, reschedule |
| `/api/payments/` | `stripe_payments` | create-intent, webhook, refunds, saved-methods |
| `/api/astrology/` | `astrology` | birth-profile, natal-chart, transits, dasha, nakshatra, insights, chat, access, festival-calendar |
| `/api/family-tree/` | `family_tree` | members, relationships |
| `/api/blogs/` | `blogs` | CRUD for blog posts |
| `/docs/` | drf-spectacular | Swagger UI |
| `/redoc/` | drf-spectacular | ReDoc |
| `/schema/` | drf-spectacular | Raw OpenAPI JSON |

---

## Role-Based Access Control

```mermaid
graph LR
    subgraph Roles
        STUDENT["STUDENT"]
        TEACHER["TEACHER"]
        BOTH["BOTH"]
        ADMIN["ADMIN"]
    end

    STUDENT -->|Can| SB["Book sessions\nView own astrology\nGrant dashboard access"]
    TEACHER -->|Can| TB["Post gigs\nManage availability\nView student dashboards\nCreate guest profiles"]
    BOTH -->|Can| SB
    BOTH -->|Can| TB
    ADMIN -->|Can| AB["Django admin\nApprove refunds\nVerify teachers\nManage AI prompt configs"]
```

**Role elevation flow:**
1. New user signs up → `role = null`
2. Calls `POST /api/set-role/` with `{"role": "STUDENT"}` or `{"role": "TEACHER"}`
3. If they later add the other role → automatically upgraded to `BOTH`
4. `GET /api/accounts/profiles/me/roles/` is the source of truth (with self-healing DB correction)

---

## External Service Integration Map

| Service | Used By | Purpose |
|---|---|---|
| **Supabase Auth (JWKS)** | `core.authentication` | JWT signature verification (cached) |
| **Supabase DB** | All apps | Primary PostgreSQL database |
| **Supabase Storage** | `accounts` (chat files), `blogs` (thumbnails) | File storage (user uploads, blog images) |
| **Google Gemini AI** | `astrology` | AI-generated astrological insight text |
| **astrology-api.io** | `astrology.services.AstrologyAPIClient` | Vedic chart calculation (natal, transit, dasha, etc.) |
| **Stripe** | `stripe_payments` | Payment intents, webhooks, refunds, saved cards |
| **Zoom (S2S OAuth)** | `bookings.zoom_service` | Auto-create meeting rooms on booking confirmation |
| **Resend** | `chat.services.email` | Transactional email (notifications) |
| **Google OAuth** | `core.views` | One-tap / OAuth sign-in |

---

## Database Schema Relationships (Cross-Module)

```mermaid
erDiagram
    User ||--o| UserProfile : profile
    UserProfile ||--o| TeacherProfile : teacher_ext
    TeacherProfile ||--o{ Gig : gigs
    TeacherProfile ||--o{ Blog : blogs
    User ||--o| BirthProfile : birth_profile
    User ||--o| StripeCustomer : stripe_customer
    User ||--o{ SessionBooking : booked_sessions
    User ||--o{ SessionBooking : teaching_sessions
    SessionBooking ||--|| Payment : payment
    Payment ||--o{ RefundRequest : refund_requests
    BirthProfile ||--o| NatalChartCache : natal_cache
    BirthProfile ||--o{ TransitCache : transit_caches
    BirthProfile ||--o{ AstrologyInsight : insights
    BirthProfile ||--o{ AstrologyChat : chats
    BirthProfile ||--o| NakshatraPredictionCache : nakshatra_cache
    User ||--o{ AstrologyDashboardAccess : astrology_access_grants
    User ||--o{ AstrologyDashboardAccess : astrology_access_received
    User ||--o{ FamilyMember : family_members
    Gig ||--o{ SessionBooking : bookings
```

---

## Key Architectural Decisions

| Decision | Rationale |
|---|---|
| **Supabase Auth only** — Django doesn't store passwords | Single auth source of truth; enables Google OAuth, magic links, etc. without extra Django packages |
| **Field-level encryption** on birth data | PII protection for sensitive birth details even if DB is compromised |
| **Multi-tier caching** for astrology | Natal chart data never changes — cache forever. Transit data changes daily. Cuts API costs significantly. |
| **Analyzer pattern** (27 focused files) | Each astrology category lives in its own file with its own prompt builder — easy to add/modify without touching others |
| **Role = `BOTH`** | Allows a single account to be both a teacher and student (e.g. astrologer who also takes language courses) |
| **`AstrologyDashboardAccess`** as explicit grant | Student explicitly grants teacher access rather than implicit role-based read — privacy first |
| **drf-spectacular sidecar** | Swagger/ReDoc assets served locally, no CDN dependency, works offline |
