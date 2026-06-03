import logging
import time
import pytz
from datetime import datetime

logger = logging.getLogger(__name__)

# Gemini Free Tier allows ~15 Requests Per Minute.
# We use exponential backoff only when a rate-limit error is detected,
# rather than sleeping blindly between every call.
_RATE_LIMIT_BASE_DELAY = 5     # seconds to wait after first 429
_RATE_LIMIT_MAX_DELAY = 60     # cap on backoff ceiling
_RATE_LIMIT_MAX_RETRIES = 4    # max attempts per category


def _is_rate_limit_error(exc: Exception) -> bool:
    """Heuristic check for Gemini 429 / resource-exhausted errors."""
    msg = str(exc).lower()
    return "429" in msg or "resource_exhausted" in msg or "rate" in msg


def _generate_insight_with_backoff(category: str, data: dict) -> str:
    """
    Call GeminiAIService.generate_insight with exponential backoff on
    rate-limit errors. Raises the last exception if all retries are exhausted.
    """
    from astrology.services import GeminiAIService

    delay = _RATE_LIMIT_BASE_DELAY
    for attempt in range(1, _RATE_LIMIT_MAX_RETRIES + 1):
        try:
            return GeminiAIService.generate_insight(category, data)
        except Exception as exc:
            if _is_rate_limit_error(exc) and attempt < _RATE_LIMIT_MAX_RETRIES:
                wait = min(delay, _RATE_LIMIT_MAX_DELAY)
                logger.warning(
                    f"Gemini rate-limit hit for category '{category}' "
                    f"(attempt {attempt}/{_RATE_LIMIT_MAX_RETRIES}). "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
                delay *= 2  # exponential backoff
            else:
                raise


def generate_all_insights_async(birth_profile_id: int):
    """
    Background task to generate all astrology insights for a given BirthProfile.
    Uses exponential backoff to handle Gemini API rate limits gracefully
    instead of a fixed sleep between every request.
    """
    from astrology.models import BirthProfile, NatalChartCache, TransitCache, AstrologyInsight
    from astrology.services import AstrologyAPIClient

    logger.info(f"Starting background async task to generate insights for BirthProfile ID: {birth_profile_id}")

    try:
        profile = BirthProfile.objects.select_related("user").get(id=birth_profile_id)
    except BirthProfile.DoesNotExist:
        logger.error(f"Generate Insights Task Failed: BirthProfile {birth_profile_id} not found.")
        return

    client = AstrologyAPIClient()

    # 1. Fetch base Natal Chart Data
    try:
        birth_details = client.get_birth_details(profile)
        divisional = client.get_divisional_chart(profile)

        # Update Timezone based on API response
        timezone_str = (
            birth_details.get("data", {})
            .get("calculation_info", {})
            .get("location", {})
            .get("timezone", "")
        )
        if timezone_str and not profile.timezone_str:
            profile.timezone_str = timezone_str
            profile.save(update_fields=["timezone_str"])

        # Cache the base data
        natal_cache, _ = NatalChartCache.objects.update_or_create(
            birth_profile=profile,
            defaults={
                "birth_details_data": birth_details,
                "divisional_data": divisional,
            }
        )
    except Exception as e:
        logger.error(f"Task Failed: Could not fetch base natal info for profile {birth_profile_id}. Error: {str(e)}")
        return

    # 2. Fetch extended data required by various Gemini prompts
    try:
        try:
            ashtakvarga = client.get_ashtakvarga(profile)
        except Exception as e:
            logger.error(f"Failed fetching ashtakvarga: {e}")
            raise

        try:
            dasha = client.get_vimshottari_dasha(profile)
        except Exception as e:
            logger.error(f"Failed fetching vimshottari dasha: {e}")
            raise

        try:
            kp_system = client.get_kp_system(profile)
        except Exception as e:
            logger.error(f"Failed fetching kp system: {e}")
            raise

        try:
            transit_data = client.get_transit(profile)
        except Exception as e:
            logger.error(f"Failed fetching transit data: {e}")
            raise

        # Update natal cache with extended data
        natal_cache.ashtakvarga_data = ashtakvarga
        natal_cache.dasha_data = dasha
        natal_cache.kp_data = kp_system
        natal_cache.save()

        # Update Transit Cache (valid for current day)
        tz = pytz.timezone(profile.timezone_str) if profile.timezone_str else pytz.utc
        today_local = datetime.now(tz).date()

        TransitCache.objects.update_or_create(
            birth_profile=profile,
            cached_for_date=today_local,
            defaults={
                "transit_data": transit_data,
            }
        )
    except Exception as e:
        logger.error(f"Task Failed: Could not fetch extended API info for profile {birth_profile_id}. Error: {str(e)}")
        return

    # 3. Assemble complete data structure to pass to Gemini
    data_to_pass = {
        "birth_details": natal_cache.birth_details_data,
        "divisional_data": natal_cache.divisional_data,
        "ashtakvarga": natal_cache.ashtakvarga_data,
        "dasha": natal_cache.dasha_data,
        "kp_system": natal_cache.kp_data,
        "transits": transit_data,
        # Personal profile context — used by marriage analysis builder
        "profile_context": {
            "name": profile.display_name,
            "gender": (profile.user.gender if profile.user else None),
            "birth_year": profile.birth_year,
            "birth_month": profile.birth_month,
            "birth_day": profile.birth_day,
            "birth_hour": profile.birth_hour,
            "birth_minute": profile.birth_minute,
            "city": profile.city,
            "country_code": profile.country_code,
            "marriage_date": profile.marriage_date,
            "kids": profile.kids,
            "comments": profile.comments,
        },
    }

    # 4. Iterate over all valid categories
    categories = [c[0] for c in AstrologyInsight.CATEGORY_CHOICES]
    logger.info(f"Generating {len(categories)} insights for profile {birth_profile_id}...")

    success_count = 0
    from django.core.cache import cache

    for category in categories:
        # Check if insight already exists to avoid redundant calls
        if AstrologyInsight.objects.filter(birth_profile=profile, category=category).exists():
            continue

        lock_key = f"generating_insight_{profile.id}_{category}"
        if cache.get(lock_key):
            # Currently being generated by a foreground view, skip it
            continue

        # Grab the lock
        cache.set(lock_key, True, timeout=60)

        try:
            logger.info(f"Generating insight: {category} for profile {birth_profile_id}")
            # Use backoff retry — only pauses when Gemini signals rate limiting
            generated_text = _generate_insight_with_backoff(category, data_to_pass)

            AstrologyInsight.objects.create(
                birth_profile=profile,
                category=category,
                insight_text=generated_text
            )
            success_count += 1
            logger.info(f"Successfully generated and cached insight: {category}")

        except Exception as e:
            logger.error(f"Failed to generate insight '{category}' for profile {birth_profile_id}: {str(e)}")
            # Continue to the next category even if one fails
        finally:
            cache.delete(lock_key)

    logger.info(f"Finished background insight generation. Total successful: {success_count}/{len(categories)}.")


