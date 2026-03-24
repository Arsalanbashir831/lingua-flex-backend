"""
AstrologyAPIClient — thin wrapper around api.astrology-api.io v3 Vedic endpoints.

All methods return the parsed JSON response dict directly.
Raises AstrologyAPIError on any failure (non-2xx status, network error, etc.).
"""
import requests
from django.conf import settings


class AstrologyAPIError(Exception):
    """Raised when the external astrology API returns an error."""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class AstrologyAPIClient:
    BASE_URL = "https://api.astrology-api.io/api/v3/vedic"

    def __init__(self):
        self.token = getattr(settings, 'ASTROLOGY_API_KEY', '')

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }

    def _subject_payload(self, profile) -> dict:
        """
        Builds the 'subject' block expected by the API.
        The user's full name is derived from the linked User model.
        """
        name = profile.user.get_full_name() or profile.user.email
        return {
            "name": name,
            "birth_data": {
                "year": profile.birth_year,
                "month": profile.birth_month,
                "day": profile.birth_day,
                "hour": profile.birth_hour,
                "minute": profile.birth_minute,
                "city": profile.city,
                "country_code": profile.country_code,
            }
        }

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=15)
        except requests.RequestException as e:
            raise AstrologyAPIError(f"Network error calling {endpoint}: {e}")

        if not resp.ok:
            raise AstrologyAPIError(
                f"Astrology API error [{resp.status_code}]: {resp.text}",
                status_code=resp.status_code
            )

        data = resp.json()
        if not data.get('success'):
            raise AstrologyAPIError(f"Astrology API returned success=false: {data}")

        return data

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_birth_details(self, profile) -> dict:
        """
        Calls POST /vedic/birth-details.
        Returns full planet positions, nakshatra, ascendant, and ayanamsa info.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "options": {
                "ayanamsa": "lahiri",
                "language": "en"
            }
        }
        return self._post("birth-details", payload)

    def get_divisional_chart(self, profile) -> dict:
        """
        Calls POST /vedic/divisional-chart requesting D1 (Rashi) and D9 (Navamsa).
        Returns planet positions in each chart.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "charts": ["D1", "D9"]
        }
        return self._post("divisional-chart", payload)

    def get_transit(self, profile) -> dict:
        """
        Calls POST /vedic/transit.
        Returns current planetary transits relative to the natal Moon.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "options": {
                "language": "en"
            }
        }
        return self._post("transit", payload)
