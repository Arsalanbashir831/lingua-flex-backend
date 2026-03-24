"""
Vedic Astrology views.

Three views:
  1. BirthProfileView — GET / POST / PUT to create or update birth data
  2. NatalChartView   — GET combined D1+D9 + birth-details, cached permanently
  3. TransitView      — GET today's transits, invalidated on local day change (no cron)
"""
from datetime import datetime

import logging
import pytz
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import BirthProfile, NatalChartCache, TransitCache
from .serializers import BirthProfileSerializer
from .services import AstrologyAPIClient, AstrologyAPIError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ZODIAC_SIGNS = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir",
    "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"
]

SIGN_LORDS = {
    "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
    "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
    "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter"
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
    asc_pos = next((p for p in positions if p.get('planet') == 'Ascendant'), None)
    asc_sign = asc_pos.get('sign', 'Ari') if asc_pos else 'Ari'
    
    planet_map = {p.get('planet'): p for p in full_planets}
    graha_details = []
    bhava_details = {i: {"bhava": i, "residents": [], "owner": "", "rashi": ""} for i in range(1, 13)}
    
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
        p_name = pos.get('planet')
        p_sign = pos.get('sign')
        
        if p_name == 'Ascendant':
            continue
            
        house_num = _calculate_house(asc_sign, p_sign)
        
        if 1 <= house_num <= 12:
            bhava_details[house_num]["residents"].append(p_name)
            
        full_p = planet_map.get(p_name, {})
        
        # Which houses does this planet own in this specific chart?
        ruled_houses = [h_num for h_num, h_data in bhava_details.items() if h_data["owner"] == p_name]
                
        graha_details.append({
            "graha": p_name,
            "longitude_rashi": p_sign,
            "longitude_degree": pos.get('degree'),
            "current_bhava": house_num,
            "rules_bhavas": ruled_houses,
            "nakshatra": full_p.get('nakshatra'),
            "nakshatra_pada": full_p.get('nakshatra_pada'),
            "nakshatra_lord": full_p.get('nakshatra_lord'),
            "nakshatra_sublord": full_p.get('nakshatra_sublord'),
        })
        
    return {
        "graha_details": graha_details,
        "bhava_details": list(bhava_details.values())
    }

def _is_transit_stale(cache: TransitCache, timezone_str: str) -> bool:
    """
    Returns True if the cached transit date no longer matches today's date
    in the user's local timezone. Falls back to UTC if no timezone stored yet.
    """
    tz = pytz.timezone(timezone_str) if timezone_str else pytz.utc
    today_local = datetime.now(tz).date()
    return cache.cached_for_date != today_local


def _build_natal_response(birth_details: dict, divisional: dict, profile: BirthProfile) -> dict:
    """
    Shapes the raw API responses into a clean, frontend-friendly payload
    that carries everything the circular chart needs, plus structured UI tables.
    """
    bd_data  = birth_details.get('data', {})
    div_data = divisional.get('data', {})

    # Extract D1 and D9 positions from the divisional chart response
    charts    = {c['chart']: c for c in div_data.get('charts', [])}
    d1_chart  = charts.get('D1', {})
    d9_chart  = charts.get('D9', {})
    
    planets_list = bd_data.get('planets', [])
    
    d1_tables = _build_ui_tables(d1_chart.get('positions', []), planets_list)
    d9_tables = _build_ui_tables(d9_chart.get('positions', []), planets_list)

    return {
        'birth_profile': BirthProfileSerializer(profile).data,
        'planets': planets_list,
        'ascendant': bd_data.get('ascendant'),
        'moon_sign': bd_data.get('moon_sign'),
        'sun_sign': bd_data.get('sun_sign'),
        'nakshatra': bd_data.get('nakshatra'),
        'ayanamsa': bd_data.get('ayanamsa'),
        'ayanamsa_value': bd_data.get('ayanamsa_value'),
        'calculation_info': bd_data.get('calculation_info'),
        
        'd1_chart': {
            'name': d1_chart.get('name', 'Rashi'),
            'purpose': d1_chart.get('purpose', 'Overall life and personality'),
            'positions': d1_chart.get('positions', []),
            'graha_details': d1_tables['graha_details'],
            'bhava_details': d1_tables['bhava_details'],
        },
        'd9_chart': {
            'name': d9_chart.get('name', 'Navamsa'),
            'purpose': d9_chart.get('purpose', 'Marriage and dharma'),
            'positions': d9_chart.get('positions', []),
            'graha_details': d9_tables['graha_details'],
            'bhava_details': d9_tables['bhava_details'],
        },
        'vargottama_planets': div_data.get('vargottama_planets', []),
    }


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class BirthProfileView(APIView):
    """
    GET  — Retrieve the authenticated user's birth profile
    POST — Create (fails if already exists; use PUT to update)
    PUT  — Update existing birth profile (also clears cached charts so they
           are recalculated on the next natal-chart request)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.birth_profile
        except BirthProfile.DoesNotExist:
            return Response(
                {'detail': 'No birth profile found. Please create one first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(BirthProfileSerializer(profile).data)

    def post(self, request):
        if BirthProfile.objects.filter(user=request.user).exists():
            return Response(
                {'detail': 'Birth profile already exists. Use PUT to update it.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = BirthProfileSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        profile = serializer.save(user=request.user)
        return Response(BirthProfileSerializer(profile).data, status=status.HTTP_201_CREATED)

    def put(self, request):
        try:
            profile = request.user.birth_profile
        except BirthProfile.DoesNotExist:
            return Response(
                {'detail': 'No birth profile found. Use POST to create one.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = BirthProfileSerializer(profile, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # Clear caches — birth data changed so charts must be recomputed
        NatalChartCache.objects.filter(birth_profile=profile).delete()
        TransitCache.objects.filter(birth_profile=profile).delete()
        profile = serializer.save(timezone_str='')  # reset timezone too
        return Response(BirthProfileSerializer(profile).data)


class NatalChartView(APIView):
    """
    GET — Returns combined D1 + D9 chart data plus full planet details.

    Data is computed once (on first request) and cached permanently in
    NatalChartCache. Subsequent calls are DB-only (no external API hit).
    timezone_str is backfilled from the API response on first call.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.birth_profile
        except BirthProfile.DoesNotExist:
            return Response(
                {'detail': 'Please create your birth profile first via POST /api/astrology/birth-profile/'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Return from cache if available
        try:
            cache = profile.natal_cache
            msg = f"Natal chart retrieved from DATABASE cache for user: {request.user.email}"
            logger.info(msg)
            return Response(_build_natal_response(
                cache.birth_details_data,
                cache.divisional_data,
                profile
            ))
        except NatalChartCache.DoesNotExist:
            msg = f"Natal chart CACHE MISS for user: {request.user.email}. Calling Astrology.io API..."
            logger.info(msg)
            pass

        # Cache miss — call the external API
        client = AstrologyAPIClient()
        try:
            birth_details = client.get_birth_details(profile)
            divisional    = client.get_divisional_chart(profile)
        except AstrologyAPIError as e:
            return Response(
                {'detail': f'Astrology API error: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Back-fill timezone from the API response (only available here)
        timezone_str = (
            birth_details.get('data', {})
            .get('calculation_info', {})
            .get('location', {})
            .get('timezone', '')
        )
        if timezone_str and not profile.timezone_str:
            profile.timezone_str = timezone_str
            profile.save(update_fields=['timezone_str'])

        # Persist cache
        NatalChartCache.objects.create(
            birth_profile=profile,
            birth_details_data=birth_details,
            divisional_data=divisional,
        )

        return Response(_build_natal_response(birth_details, divisional, profile))


class TransitView(APIView):
    """
    GET — Returns today's planetary transits relative to the natal Moon.

    Cache invalidation strategy (no cron):
      - On each request, compare cached_for_date with today in the user's
        local timezone (stored in BirthProfile.timezone_str).
      - If the dates differ → call the API and refresh the cache.
      - If timezone_str is not yet set (natal chart not fetched) → fall back to UTC.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = request.user.birth_profile
        except BirthProfile.DoesNotExist:
            return Response(
                {'detail': 'Please create your birth profile first via POST /api/astrology/birth-profile/'},
                status=status.HTTP_404_NOT_FOUND
            )

        tz = pytz.timezone(profile.timezone_str) if profile.timezone_str else pytz.utc
        today_local = datetime.now(tz).date()

        # Try cache
        try:
            cache = profile.transit_cache
            if not _is_transit_stale(cache, profile.timezone_str):
                msg = f"Transit data retrieved from DATABASE cache for user: {request.user.email}"
                logger.info(msg)
                print(f">>> {msg}")
                return Response(self._shape_response(cache.transit_data))
        except TransitCache.DoesNotExist:
            cache = None

        # Cache miss or stale — call the API
        msg = f"Transit data CACHE MISS (or stale) for user: {request.user.email}. Calling Astrology.io API..."
        logger.info(msg)
        print(f">>> {msg}")
        client = AstrologyAPIClient()
        try:
            transit = client.get_transit(profile)
        except AstrologyAPIError as e:
            return Response(
                {'detail': f'Astrology API error: {str(e)}'},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # Upsert cache
        if cache is None:
            TransitCache.objects.create(
                birth_profile=profile,
                transit_data=transit,
                cached_for_date=today_local,
            )
        else:
            cache.transit_data    = transit
            cache.cached_for_date = today_local
            cache.save()

        return Response(self._shape_response(transit))

    def _shape_response(self, raw: dict) -> dict:
        data = raw.get('data', {})
        return {
            'transit_date': data.get('transit_date'),
            'natal_moon': data.get('natal_moon'),
            'transits': data.get('transits', []),
            'summary': data.get('summary'),
            'ayanamsa': data.get('ayanamsa'),
        }
