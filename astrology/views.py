"""
Vedic Astrology views.

Views:
  1. BirthProfileView            — GET / POST / PUT to manage birth data
  2. NatalChartView              — GET combined D1+D9, cached permanently
  3. TransitView                 — GET today's transits, invalidated daily
  4. AstrologyInsightView        — GET Gemini AI insight per category
  5. AstrologyAccessView         — Student manages access grants (GET/POST)
  6. AstrologyAccessRevokeView   — Student revokes a specific grant (DELETE)
  7. TeacherStudentDashboardsView — Teacher lists students they can view (GET)
"""

from datetime import datetime

import logging
import pytz
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import (
    BirthProfile,
    NatalChartCache,
    TransitCache,
    AstrologyInsight,
    AstrologyDashboardAccess,
)
from .serializers import (
    BirthProfileSerializer,
    AstrologyAccessSerializer,
    StudentDashboardSummarySerializer,
)
from .services import AstrologyAPIClient, AstrologyAPIError, GeminiAIService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ZODIAC_SIGNS = [
    "Ari",
    "Tau",
    "Gem",
    "Can",
    "Leo",
    "Vir",
    "Lib",
    "Sco",
    "Sag",
    "Cap",
    "Aqu",
    "Pis",
]

SIGN_LORDS = {
    "Ari": "Mars",
    "Tau": "Venus",
    "Gem": "Mercury",
    "Can": "Moon",
    "Leo": "Sun",
    "Vir": "Mercury",
    "Lib": "Venus",
    "Sco": "Mars",
    "Sag": "Jupiter",
    "Cap": "Saturn",
    "Aqu": "Saturn",
    "Pis": "Jupiter",
}


def _calculate_house(asc_sign: str, planet_sign: str) -> int:
    """Calculates the house number (1-12) based on Ascendant and Planet signs."""
    try:
        asc_idx = ZODIAC_SIGNS.index(asc_sign)
        plt_idx = ZODIAC_SIGNS.index(planet_sign)
        return ((plt_idx - asc_idx) % 12) + 1
    except ValueError:
        return 1


def _build_ui_tables(positions: list, full_planets: list) -> dict:
    """Builds Graha and Bhava details explicitly mapped for the UI."""
    asc_pos = next((p for p in positions if p.get("planet") == "Ascendant"), None)
    asc_sign = asc_pos.get("sign", "Ari") if asc_pos else "Ari"

    planet_map = {p.get("planet"): p for p in full_planets}
    graha_details = []
    bhava_details = {
        i: {"bhava": i, "residents": [], "owner": "", "rashi": ""} for i in range(1, 13)
    }

    # Pre-fill Bhava details based on Ascendant
    try:
        asc_idx = ZODIAC_SIGNS.index(asc_sign)
        for i in range(12):
            sign = ZODIAC_SIGNS[(asc_idx + i) % 12]
            bhava_details[i + 1]["rashi"] = sign
            bhava_details[i + 1]["owner"] = SIGN_LORDS.get(sign, "")
    except ValueError:
        pass

    for pos in positions:
        p_name = pos.get("planet")
        p_sign = pos.get("sign")

        if p_name == "Ascendant":
            continue

        house_num = _calculate_house(asc_sign, p_sign)

        if 1 <= house_num <= 12:
            bhava_details[house_num]["residents"].append(p_name)

        full_p = planet_map.get(p_name, {})

        # Which houses does this planet own in this specific chart?
        ruled_houses = [
            h_num
            for h_num, h_data in bhava_details.items()
            if h_data["owner"] == p_name
        ]

        graha_details.append(
            {
                "graha": p_name,
                "longitude_rashi": p_sign,
                "longitude_degree": pos.get("degree"),
                "current_bhava": house_num,
                "rules_bhavas": ruled_houses,
                "nakshatra": full_p.get("nakshatra"),
                "nakshatra_pada": full_p.get("nakshatra_pada"),
                "nakshatra_lord": full_p.get("nakshatra_lord"),
                "nakshatra_sublord": full_p.get("nakshatra_sublord"),
            }
        )

    return {
        "graha_details": graha_details,
        "bhava_details": list(bhava_details.values()),
    }


def _is_transit_stale(cache: TransitCache, timezone_str: str) -> bool:
    """
    Returns True if the cached transit date no longer matches today's date
    in the user's local timezone. Falls back to UTC if no timezone stored yet.
    """
    tz = pytz.timezone(timezone_str) if timezone_str else pytz.utc
    today_local = datetime.now(tz).date()
    return cache.cached_for_date != today_local


def _build_natal_response(
    birth_details: dict, divisional: dict, profile: BirthProfile
) -> dict:
    """
    Shapes the raw API responses into a clean, frontend-friendly payload
    that carries everything the circular chart needs, plus structured UI tables.
    """
    bd_data = birth_details.get("data", {})
    div_data = divisional.get("data", {})

    # Extract D1 and D9 positions from the divisional chart response
    charts = {c["chart"]: c for c in div_data.get("charts", [])}
    d1_chart = charts.get("D1", {})
    d9_chart = charts.get("D9", {})

    planets_list = bd_data.get("planets", [])

    d1_tables = _build_ui_tables(d1_chart.get("positions", []), planets_list)
    d9_tables = _build_ui_tables(d9_chart.get("positions", []), planets_list)

    return {
        "birth_profile": BirthProfileSerializer(profile).data,
        "planets": planets_list,
        "ascendant": bd_data.get("ascendant"),
        "moon_sign": bd_data.get("moon_sign"),
        "sun_sign": bd_data.get("sun_sign"),
        "nakshatra": bd_data.get("nakshatra"),
        "ayanamsa": bd_data.get("ayanamsa"),
        "ayanamsa_value": bd_data.get("ayanamsa_value"),
        "calculation_info": bd_data.get("calculation_info"),
        "d1_chart": {
            "name": d1_chart.get("name", "Rashi"),
            "purpose": d1_chart.get("purpose", "Overall life and personality"),
            "positions": d1_chart.get("positions", []),
            "graha_details": d1_tables["graha_details"],
            "bhava_details": d1_tables["bhava_details"],
        },
        "d9_chart": {
            "name": d9_chart.get("name", "Navamsa"),
            "purpose": d9_chart.get("purpose", "Marriage and dharma"),
            "positions": d9_chart.get("positions", []),
            "graha_details": d9_tables["graha_details"],
            "bhava_details": d9_tables["bhava_details"],
        },
        "vargottama_planets": div_data.get("vargottama_planets", []),
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------


def _resolve_profile(request):
    """
    Resolves which user's BirthProfile to use for the current request.

    - If `?student_id=X` is provided:
        1. Verifies the request user is a teacher (role==TEACHER).
        2. Verifies there is an active AstrologyDashboardAccess grant from
           the target student to the requesting teacher.
        3. Returns that student's BirthProfile.
    - Otherwise returns request.user's own BirthProfile.

    Returns (profile, error_response) where exactly one of them is None.
    """
    from core.models import User

    student_id = request.query_params.get("student_id")
    if not student_id:
        try:
            return request.user.birth_profile, None
        except BirthProfile.DoesNotExist:
            return None, Response(
                {"detail": "No birth profile found. Please create one first."},
                status=status.HTTP_404_NOT_FOUND,
            )

    # Teacher-delegated access path
    if request.user.role != "TEACHER":
        return None, Response(
            {"detail": "Only teachers can view other users' dashboards."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        target_student = User.objects.get(pk=student_id)
    except User.DoesNotExist:
        return None, Response(
            {"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND
        )

    has_access = AstrologyDashboardAccess.objects.filter(
        student=target_student, teacher=request.user
    ).exists()
    if not has_access:
        return None, Response(
            {
                "detail": "Access denied. The student has not granted you dashboard access."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        return target_student.birth_profile, None
    except BirthProfile.DoesNotExist:
        return None, Response(
            {"detail": "The student has not created a birth profile yet."},
            status=status.HTTP_404_NOT_FOUND,
        )


class BirthProfileView(APIView):
    """
    GET  — Retrieve the authenticated user's birth profile
    POST — Create (fails if already exists; use PUT to update)
    PUT  — Update existing birth profile (also clears cached charts so they
           are recalculated on the next natal-chart request)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, err = _resolve_profile(request)
        if err:
            return err
        return Response(BirthProfileSerializer(profile).data)

    def post(self, request):
        if BirthProfile.objects.filter(user=request.user).exists():
            return Response(
                {"detail": "Birth profile already exists. Use PUT to update it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = BirthProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        profile = serializer.save(user=request.user)

        # Trigger background insight generation
        import threading
        from .tasks import generate_all_insights_async
        threading.Thread(target=generate_all_insights_async, args=(profile.id,)).start()

        return Response(
            BirthProfileSerializer(profile).data, status=status.HTTP_201_CREATED
        )

    def put(self, request):
        try:
            profile = request.user.birth_profile
        except BirthProfile.DoesNotExist:
            return Response(
                {"detail": "No birth profile found. Use POST to create one."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BirthProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Clear caches — birth data changed so charts must be recomputed
        NatalChartCache.objects.filter(birth_profile=profile).delete()
        TransitCache.objects.filter(birth_profile=profile).delete()
        AstrologyInsight.objects.filter(birth_profile=profile).delete()
        profile = serializer.save(timezone_str="")  # reset timezone too

        # Trigger background insight generation
        import threading
        from .tasks import generate_all_insights_async
        threading.Thread(target=generate_all_insights_async, args=(profile.id,)).start()

        return Response(BirthProfileSerializer(profile).data)


class NatalChartView(APIView):
    """
    GET — Returns combined D1 + D9 chart data plus full planet details.

    Supports ?student_id=X for teachers with delegated access.
    Data is computed once (on first request) and cached permanently in
    NatalChartCache. Subsequent calls are DB-only (no external API hit).
    timezone_str is backfilled from the API response on first call.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, err = _resolve_profile(request)
        if err:
            return err

        # Return from cache if available
        try:
            cache = profile.natal_cache
            msg = f"Natal chart retrieved from DATABASE cache for user: {profile.user.email}"
            logger.info(msg)
            return Response(
                _build_natal_response(
                    cache.birth_details_data, cache.divisional_data, profile
                )
            )
        except NatalChartCache.DoesNotExist:
            msg = f"Natal chart CACHE MISS for user: {profile.user.email}. Calling Astrology.io API..."
            logger.info(msg)
            pass

        # Cache miss — call the external API
        client = AstrologyAPIClient()
        try:
            birth_details = client.get_birth_details(profile)
            divisional = client.get_divisional_chart(profile)
        except AstrologyAPIError as e:
            return Response(
                {"detail": f"Astrology API error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Back-fill timezone from the API response (only available here)
        timezone_str = (
            birth_details.get("data", {})
            .get("calculation_info", {})
            .get("location", {})
            .get("timezone", "")
        )
        if timezone_str and not profile.timezone_str:
            profile.timezone_str = timezone_str
            profile.save(update_fields=["timezone_str"])

        # Persist cache
        NatalChartCache.objects.update_or_create(
            birth_profile=profile,
            defaults={
                "birth_details_data": birth_details,
                "divisional_data": divisional,
            }
        )

        return Response(_build_natal_response(birth_details, divisional, profile))


class TransitView(APIView):
    """
    GET — Returns today's planetary transits relative to the natal Moon.

    Supports ?student_id=X for teachers with delegated access.
    Cache invalidation strategy (no cron):
      - On each request, compare cached_for_date with today in the user's
        local timezone (stored in BirthProfile.timezone_str).
      - If the dates differ → call the API and refresh the cache.
      - If timezone_str is not yet set (natal chart not fetched) → fall back to UTC.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, err = _resolve_profile(request)
        if err:
            return err

        tz = pytz.timezone(profile.timezone_str) if profile.timezone_str else pytz.utc
        today_local = datetime.now(tz).date()

        # Try cache
        try:
            cache = profile.transit_cache
            if not _is_transit_stale(cache, profile.timezone_str):
                msg = f"Transit data retrieved from DATABASE cache for user: {profile.user.email}"
                logger.info(msg)
                return Response(self._shape_response(cache.transit_data))
        except TransitCache.DoesNotExist:
            cache = None

        # Cache miss or stale — call the API
        msg = f"Transit data CACHE MISS (or stale) for user: {profile.user.email}. Calling Astrology.io API..."
        logger.info(msg)

        client = AstrologyAPIClient()
        try:
            transit = client.get_transit(profile)
        except AstrologyAPIError as e:
            return Response(
                {"detail": f"Astrology API error: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Upsert cache
        if cache is None:
            TransitCache.objects.update_or_create(
                birth_profile=profile,
                defaults={
                    "transit_data": transit,
                    "cached_for_date": today_local,
                }
            )
        else:
            cache.transit_data = transit
            cache.cached_for_date = today_local
            cache.save()

        return Response(self._shape_response(transit))

    def _shape_response(self, raw: dict) -> dict:
        data = raw.get("data", {})
        return {
            "transit_date": data.get("transit_date"),
            "natal_moon": data.get("natal_moon"),
            "transits": data.get("transits", []),
            "summary": data.get("summary"),
            "ayanamsa": data.get("ayanamsa"),
        }


class AstrologyInsightView(APIView):
    """
    GET — Returns a cached Gemini AI insight for the specified category.

    Supports ?student_id=X for teachers with delegated access.
    If it's a cache miss, fetches required extended data and generates via Gemini.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, category):
        valid_categories = [c[0] for c in AstrologyInsight.CATEGORY_CHOICES]
        if category not in valid_categories:
            return Response(
                {"detail": f"Invalid category. Valid options: {valid_categories}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, err = _resolve_profile(request)
        if err:
            return err

        # 1. Check DB Cache
        insight = AstrologyInsight.objects.filter(
            birth_profile=profile, category=category
        ).first()
        if insight:
            msg = f"AI Insight ({category}) CACHE HIT for user: {profile.user.email}"
            logger.info(msg)
            return Response(
                {"category": category, "insight_text": insight.insight_text}
            )

        # Check if the background task is currently generating this insight
        from django.core.cache import cache
        import time

        lock_key = f"generating_insight_{profile.id}_{category}"
        if cache.get(lock_key):
            logger.info(f"Insight ({category}) for user {profile.user.email} is currently being generated in the background. Waiting...")
            # Poll for up to 30 seconds
            for _ in range(30):
                time.sleep(1)
                insight = AstrologyInsight.objects.filter(birth_profile=profile, category=category).first()
                if insight:
                    return Response({"category": category, "insight_text": insight.insight_text})
                
                # If the lock disappears but no insight exists, the background task might have failed.
                if not cache.get(lock_key):
                    break

        # 2. Cache Miss - Need to Generate
        cache.set(lock_key, True, timeout=90) # Lock it down so the background task skips it
        try:
            msg = f"AI Insight ({category}) CACHE MISS for user: {profile.user.email}. Generating with Gemini..."
            logger.info(msg)

            # Safely grab the base natal component needed to run advanced queries.
            try:
                natal_cache = profile.natal_cache
            except NatalChartCache.DoesNotExist:
                return Response(
                    {"detail": "Please fetch the base natal chart first."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            client = AstrologyAPIClient()
            data_to_pass = {
                "birth_details": natal_cache.birth_details_data,
                "divisional_data": natal_cache.divisional_data,
            }

            # 3. Lazy Load Extended API Data (Ashtakvarga, Vimshottari, KP, etc)
            try:
                if category in ["prosperity_sav", "medical"]:
                    if not natal_cache.ashtakvarga_data:
                        natal_cache.ashtakvarga_data = client.get_ashtakvarga(profile)
                    data_to_pass["ashtakvarga"] = natal_cache.ashtakvarga_data

                if category in [
                    "marriage",
                    "medical",
                    "btr",
                    "benefic_planets",
                    "malefic_planets",
                    "chart_analysis",
                ]:
                    if not natal_cache.dasha_data:
                        natal_cache.dasha_data = client.get_vimshottari_dasha(profile)
                    data_to_pass["dasha"] = natal_cache.dasha_data

                if category == "btr":
                    if not natal_cache.kp_data:
                        natal_cache.kp_data = client.get_kp_system(profile)
                    data_to_pass["kp_system"] = natal_cache.kp_data

                if category in ["marriage", "medical", "darakaraka"]:
                    from django.utils.timezone import localtime, now

                    today_local = localtime(now()).date()
                    transit_cache = TransitCache.objects.filter(
                        birth_profile=profile, cached_for_date=today_local
                    ).first()
                    if transit_cache:
                        data_to_pass["transits"] = transit_cache.transit_data
                    else:
                        transit_data = client.get_transit(profile)
                        TransitCache.objects.update_or_create(
                            birth_profile=profile,
                            defaults={
                                "transit_data": transit_data,
                                "cached_for_date": today_local,
                            }
                        )
                        data_to_pass["transits"] = transit_data

                natal_cache.save()
            except AstrologyAPIError as e:
                return Response(
                    {"detail": f"Failed to fetch extended astrology data: {str(e)}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            # 4. Invoke Gemini API
            try:
                generated_text = GeminiAIService.generate_insight(category, data_to_pass)
            except Exception as e:
                return Response(
                    {"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 5. Populate and Save Cache
            new_insight, _ = AstrologyInsight.objects.update_or_create(
                birth_profile=profile, category=category, 
                defaults={"insight_text": generated_text}
            )

            return Response(
                {"category": category, "insight_text": new_insight.insight_text}
            )
        finally:
            cache.delete(lock_key)


# ---------------------------------------------------------------------------
# Access Management Views
# ---------------------------------------------------------------------------


class AstrologyAccessView(APIView):
    """
    GET  — Student lists all teachers who have access to their dashboard.
    POST — Student grants access to a teacher (body: { "teacher_id": "..." }).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        grants = AstrologyDashboardAccess.objects.filter(
            student=request.user
        ).select_related("teacher")
        serializer = AstrologyAccessSerializer(grants, many=True)
        return Response(serializer.data)

    def post(self, request):
        from accounts.models import Gig
        from core.models import User

        teacher_id = request.data.get("teacher_id")
        if not teacher_id:
            return Response(
                {"detail": "teacher_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            teacher = User.objects.get(pk=teacher_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Teacher not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Verify the target user actually has an active astrology gig
        has_astrology_gig = Gig.objects.filter(
            teacher__user_profile__user=teacher,
            category=Gig.Category.ASTROLOGICAL_CONSULTATION,
            status=Gig.Status.ACTIVE,
        ).exists()
        if not has_astrology_gig:
            return Response(
                {"detail": "This teacher does not have an active astrology gig."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prevent self-grant
        if teacher == request.user:
            return Response(
                {"detail": "You cannot grant access to yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grant, created = AstrologyDashboardAccess.objects.get_or_create(
            student=request.user, teacher=teacher
        )
        if not created:
            return Response(
                {"detail": "Access has already been granted to this teacher."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AstrologyAccessSerializer(grant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AstrologyAccessRevokeView(APIView):
    """
    DELETE — Student revokes a specific teacher's access to their dashboard.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, teacher_id):
        deleted_count, _ = AstrologyDashboardAccess.objects.filter(
            student=request.user, teacher_id=teacher_id
        ).delete()
        if deleted_count == 0:
            return Response(
                {"detail": "No active access grant found for this teacher."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"detail": "Access revoked successfully."},
            status=status.HTTP_200_OK,
        )


class TeacherStudentDashboardsView(APIView):
    """
    GET — Teacher lists all students who have granted them dashboard access.
    Only accessible by users with role=TEACHER.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "TEACHER":
            return Response(
                {"detail": "Only teachers can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        grants = AstrologyDashboardAccess.objects.filter(
            teacher=request.user
        ).select_related("student", "student__birth_profile")
        serializer = StudentDashboardSummarySerializer(grants, many=True)
        return Response(serializer.data)
