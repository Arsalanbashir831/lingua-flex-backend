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
        self.token = getattr(settings, "ASTROLOGY_API_KEY", "")

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
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
            },
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
                status_code=resp.status_code,
            )

        data = resp.json()
        if not data.get("success"):
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
            "options": {"ayanamsa": "lahiri", "language": "en"},
        }
        return self._post("birth-details", payload)

    def get_divisional_chart(self, profile) -> dict:
        """
        Calls POST /vedic/divisional-chart.
        Returns D1, D3, D9, D12, and D30 charts for advanced AI diagnostics.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "charts": ["D1", "D3", "D9", "D12", "D30"],
        }
        return self._post("divisional-chart", payload)

    def get_transit(self, profile) -> dict:
        """
        Calls POST /vedic/transit.
        Returns current planetary transits relative to the natal Moon.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "options": {"language": "en"},
        }
        return self._post("transit", payload)

    def get_kp_system(self, profile) -> dict:
        """
        Calls POST /vedic/kp-system.
        Returns KP cusps, significators, and ruling planets.
        """
        payload = {"subject": self._subject_payload(profile)}
        return self._post("kp-system", payload)

    def get_vimshottari_dasha(self, profile) -> dict:
        """
        Calls POST /vedic/vimshottari-dasha.
        Returns Vimshottari Mahadasha/Antardasha periods based on the birth details.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "dasha_level": "antardasha",
            "options": {"language": "en"},
        }
        return self._post("vimshottari-dasha", payload)

    def get_ashtakvarga(self, profile) -> dict:
        """
        Calls POST /vedic/ashtakvarga.
        Returns SAV points and strengths for all planets and houses.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "include_sarva": True,
            "options": {"ayanamsa": "lahiri"},
        }
        return self._post("ashtakvarga", payload)


class GeminiAIError(Exception):
    """Raised when GenAI generation fails."""

    pass


class GeminiAIService:
    from .ai_prompts import (
        MENTAL_HEALTH_PROMPT,
        KP_BTR_PROMPT,
        MARRIAGE_TIMING_PROMPT,
        MASTER_SAV_PROMPT,
        PARASARI_PROMPT,
        NAVATARA_PROMPT,
        MEDICAL_PROMPT,
        DARAKARAKA_PROMPT,
    )

    PROMPTS = {
        "mental_health": MENTAL_HEALTH_PROMPT,
        "marriage": MARRIAGE_TIMING_PROMPT,
        "prosperity_sav": MASTER_SAV_PROMPT,
        "medical": MEDICAL_PROMPT,
        "btr": KP_BTR_PROMPT,
        "parasari": PARASARI_PROMPT,
        "navatara": NAVATARA_PROMPT,
        "darakaraka": DARAKARAKA_PROMPT,
    }

    @classmethod
    def generate_insight(
        cls, category: str, structured_data: dict, extra_context: dict = None
    ) -> str:
        import json
        from google import genai
        from .models import AIPromptConfiguration

        prompt_template = cls.PROMPTS.get(category)
        if not prompt_template:
            raise ValueError(f"No prompt template found for category: {category}")

        # Append custom user prompt from Admin if available
        config = AIPromptConfiguration.objects.filter(
            category=category, is_active=True
        ).first()
        if config and config.user_prompt.strip():
            # Add separation before the custom user instructions
            prompt_template = f"{prompt_template}\n\n-----------------------------------\nUSER PRIORITY FOCUS:\n{config.user_prompt.strip()}\n"

        # Categories with specific named placeholders are handled differently.
        if category == "mental_health":
            prompt = cls._build_mental_health_prompt(prompt_template, structured_data)
        elif category == "btr":
            prompt = cls._build_btr_prompt(
                prompt_template, structured_data, extra_context or {}
            )
        elif category == "marriage":
            prompt = cls._build_marriage_prompt(prompt_template, structured_data)
        elif category == "prosperity_sav":
            prompt = cls._build_sav_prompt(prompt_template, structured_data)
        elif category == "parasari":
            prompt = cls._build_parasari_prompt(prompt_template, structured_data)
        elif category == "navatara":
            prompt = cls._build_navatara_prompt(prompt_template, structured_data)
        elif category == "medical":
            prompt = cls._build_medical_prompt(prompt_template, structured_data)
        elif category == "darakaraka":
            prompt = cls._build_darakaraka_prompt(prompt_template, structured_data)
        else:
            # All other prompts use a single {astrology_data} JSON dump
            data_str = json.dumps(structured_data, indent=2)
            prompt = prompt_template.format(astrology_data=data_str)

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            raise GeminiAIError(f"Failed to generate insight from Gemini: {str(e)}")

    @staticmethod
    def _build_mental_health_prompt(template: str, structured_data: dict) -> str:
        """
        Extracts specific planet/house fields from the stored API data
        and injects them into the MENTAL_HEALTH_PROMPT named placeholders.

        Uses divisional_data (from the divisional-chart API) for D1 sign positions.
        birth_details_data contains house placements and dignity info.
        """
        # --- Parse D1 positions from divisional_data ---
        # Structure: data.charts[].positions[] where chart == "D1"
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d1_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D1":
                d1_positions = chart.get("positions", [])
                break

        # Build a flat planet map from D1
        planet_map = {}
        for pos in d1_positions:
            planet_name = pos.get("planet", "")
            planet_map[planet_name] = {
                "sign": pos.get("sign", "N/A"),
                "degree": pos.get("degree", 0),
                "lord": pos.get("lord", "N/A"),
            }

        # --- Parse birth_details for house placements and dignity ---
        # Structure: data.planets[] with fields: planet, house, rashi, nakshatra, dignity
        birth_raw = structured_data.get("birth_details", {})
        birth_planets = birth_raw.get("data", {}).get("planets", [])
        house_map = {}  # planet -> house number
        dignity_map = {}  # planet -> dignity
        nakshatra_map = {}  # planet -> nakshatra

        for p in birth_planets:
            name = p.get("planet", "")
            house_map[name] = p.get("house", "N/A")
            dignity_map[name] = p.get("dignity", "N/A")
            nakshatra_map[name] = p.get("nakshatra", "N/A")

        # --- Build Lagna string ---
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")
        lagna_str = f"{lagna_sign} (Lord: {lagna_lord})"

        # --- Build Moon string ---
        moon_d1 = planet_map.get("Moon", {})
        moon_house = house_map.get("Moon", "N/A")
        # Find planets conjunct Moon (same house)
        moon_conjuncts = [
            name
            for name, h in house_map.items()
            if h == moon_house and name != "Moon" and name != "Ascendant"
        ]
        moon_str = (
            f"Sign: {moon_d1.get('sign', 'N/A')}, "
            f"House: {moon_house}, "
            f"Nakshatra: {nakshatra_map.get('Moon', 'N/A')}, "
            f"Dignity: {dignity_map.get('Moon', 'N/A')}, "
            f"Conjunct: {moon_conjuncts if moon_conjuncts else 'None'}"
        )

        # --- Build Mercury string ---
        mercury_d1 = planet_map.get("Mercury", {})
        mercury_house = house_map.get("Mercury", "N/A")
        mercury_conjuncts = [
            name
            for name, h in house_map.items()
            if h == mercury_house and name != "Mercury" and name != "Ascendant"
        ]
        mercury_str = (
            f"Sign: {mercury_d1.get('sign', 'N/A')}, "
            f"House: {mercury_house}, "
            f"Nakshatra: {nakshatra_map.get('Mercury', 'N/A')}, "
            f"Dignity: {dignity_map.get('Mercury', 'N/A')}, "
            f"Conjunct: {mercury_conjuncts if mercury_conjuncts else 'None'}"
        )

        # --- Build 4th House string ---
        # The 4th house lord is the lord of the sign that falls in house 4.
        # We derive the 4th house sign from birth_details planet data.
        house4_sign = "N/A"
        house4_lord = "N/A"
        for p in birth_planets:
            if p.get("house") == 4:
                house4_sign = p.get("rashi", "N/A")
                house4_lord = p.get("house_lord", "N/A")
                break

        house4_planets = [
            name for name, h in house_map.items() if h == 4 and name != "Ascendant"
        ]
        house4_str = (
            f"Sign: {house4_sign}, "
            f"Lord: {house4_lord}, "
            f"Planets in 4th: {house4_planets if house4_planets else 'None'}"
        )

        return template.format(
            lagna=lagna_str,
            moon=moon_str,
            mercury=mercury_str,
            house4=house4_str,
        )

    @staticmethod
    def _build_btr_prompt(
        template: str, structured_data: dict, extra_context: dict
    ) -> str:
        """
        Uses the extra_context dictionary for user-provided life event dates,
        and injects the kp_system JSON data as {astrology_data}.
        """
        import json

        kp_data_str = json.dumps(structured_data.get("kp_system", {}), indent=2)

        return template.format(
            birth_date=extra_context.get("birth_date", "Not provided"),
            birth_time=extra_context.get("birth_time", "Not provided"),
            birth_place=extra_context.get("birth_place", "Not provided"),
            marriage_date=extra_context.get("marriage_date", "Not provided"),
            childbirth_date=extra_context.get("childbirth_date", "Not provided"),
            career_date=extra_context.get("career_date", "Not provided"),
            astrology_data=kp_data_str,
        )

    # -------------------------------------------------------------------------
    # Helper: Sign order (used for computing house signs from lagna)
    # -------------------------------------------------------------------------
    _SIGN_ORDER = [
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

    @classmethod
    def _sign_of_house(cls, lagna_sign: str, house_offset: int) -> str:
        """Returns sign that falls in (lagna + house_offset - 1) position."""
        try:
            idx = cls._SIGN_ORDER.index(lagna_sign)
            return cls._SIGN_ORDER[(idx + house_offset - 1) % 12]
        except ValueError:
            return "N/A"

    @classmethod
    def _get_d1_planet_map(cls, structured_data: dict) -> dict:
        """Returns {planet_name: {sign, degree, lord}} from divisional_data D1."""
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        for chart in all_charts:
            if chart.get("chart") == "D1":
                return {p["planet"]: p for p in chart.get("positions", [])}
        return {}

    @classmethod
    def _get_birth_planets(cls, structured_data: dict) -> list:
        """Returns planet list from birth_details with house, rashi, dignity."""
        return (
            structured_data.get("birth_details", {}).get("data", {}).get("planets", [])
        )

    # -------------------------------------------------------------------------
    # Builder: Marriage Timing
    # Placeholders: lagna, house2, house7, house11, mahadasha, antardasha, dasha_sequence
    # -------------------------------------------------------------------------
    @classmethod
    def _build_marriage_prompt(cls, template: str, structured_data: dict) -> str:
        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        house2_sign = cls._sign_of_house(lagna_sign, 2)
        house7_sign = cls._sign_of_house(lagna_sign, 7)
        house11_sign = cls._sign_of_house(lagna_sign, 11)

        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha = current.get("mahadasha", "N/A")
        antardasha = current.get("antardasha", "N/A")

        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_lines.append(
                f"  {a.get('planet')} Antardasha: {a.get('start_date')} to {a.get('end_date')}{marker}"
            )
        dasha_sequence = "\n".join(dasha_lines) if dasha_lines else "Not available"

        transit_raw = structured_data.get("transits", {})
        transits_list = transit_raw.get("data", {}).get("transits", [])
        import json

        transits_str = (
            json.dumps(transits_list, indent=2) if transits_list else "Not available"
        )

        return template.format(
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            house2=house2_sign,
            house7=house7_sign,
            house11=house11_sign,
            mahadasha=mahadasha,
            antardasha=antardasha,
            dasha_sequence=dasha_sequence,
            transits=transits_str,
        )

    # -------------------------------------------------------------------------
    # Builder: SAV Prosperity
    # Placeholders: lagna, sav_house_points, saturn_house
    # -------------------------------------------------------------------------
    @classmethod
    def _build_sav_prompt(cls, template: str, structured_data: dict) -> str:
        planet_map = cls._get_d1_planet_map(structured_data)
        lagna_sign = planet_map.get("Ascendant", {}).get("sign", "N/A")
        lagna_lord = planet_map.get("Ascendant", {}).get("lord", "N/A")

        sav_raw = structured_data.get("ashtakvarga", {})
        house_breakdown = (
            sav_raw.get("data", {})
            .get("sarvashtakvarga", {})
            .get("house_breakdown", [])
        )
        sav_lines = []
        for h in house_breakdown:
            sav_lines.append(
                f"  House {h.get('house')} ({h.get('sign')}): "
                f"{h.get('total_bindus')} bindus [{h.get('strength')}] - {h.get('house_theme')}"
            )
        sav_house_points = "\n".join(sav_lines) if sav_lines else "Not available"

        # Saturn's current natal house from birth_details
        birth_planets = cls._get_birth_planets(structured_data)
        saturn_house = next(
            (
                p.get("house", "N/A")
                for p in birth_planets
                if p.get("planet") == "Saturn"
            ),
            "N/A",
        )

        return template.format(
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            sav_house_points=sav_house_points,
            saturn_house=saturn_house,
        )

    # -------------------------------------------------------------------------
    # Builder: Parasari Relationships
    # Placeholders: lagna, sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu
    # -------------------------------------------------------------------------
    @classmethod
    def _build_parasari_prompt(cls, template: str, structured_data: dict) -> str:
        planet_map = cls._get_d1_planet_map(structured_data)
        birth_planets = cls._get_birth_planets(structured_data)
        house_map = {p.get("planet"): p.get("house", "N/A") for p in birth_planets}

        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        def planet_str(name):
            p = planet_map.get(name, {})
            return (
                f"Sign: {p.get('sign', 'N/A')}, "
                f"House: {house_map.get(name, 'N/A')}, "
                f"Degree: {p.get('degree', 'N/A')}, "
                f"Lord of sign: {p.get('lord', 'N/A')}"
            )

        return template.format(
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            sun=planet_str("Sun"),
            moon=planet_str("Moon"),
            mars=planet_str("Mars"),
            mercury=planet_str("Mercury"),
            jupiter=planet_str("Jupiter"),
            venus=planet_str("Venus"),
            saturn=planet_str("Saturn"),
            rahu=planet_str("Rahu"),
            ketu=planet_str("Ketu"),
        )

    # -------------------------------------------------------------------------
    # Builder: Navatara
    # Placeholders: nakshatra, pada
    # -------------------------------------------------------------------------
    @classmethod
    def _build_navatara_prompt(cls, template: str, structured_data: dict) -> str:
        birth_planets = cls._get_birth_planets(structured_data)
        moon_nakshatra = next(
            (
                p.get("nakshatra", "N/A")
                for p in birth_planets
                if p.get("planet") == "Moon"
            ),
            "N/A",
        )
        birth_raw = structured_data.get("birth_details", {})
        birth_nakshatra = birth_raw.get("data", {}).get("birth_star", moon_nakshatra)

        return template.format(
            nakshatra=birth_nakshatra,
            pada="Not provided",
        )

    # -------------------------------------------------------------------------
    # Builder: Medical Astrology
    # Placeholders: d1_data, d9_data, d30_data, dasha
    # -------------------------------------------------------------------------
    @classmethod
    def _build_medical_prompt(cls, template: str, structured_data: dict) -> str:
        import json

        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])

        charts = {c.get("chart"): c.get("positions", []) for c in all_charts}
        d1_str = json.dumps(charts.get("D1", []), indent=2)
        d9_str = json.dumps(charts.get("D9", []), indent=2)
        d30_str = json.dumps(charts.get("D30", []), indent=2)

        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        antardasha_end = current.get("antardasha_end", "N/A")
        dasha_str = (
            f"Mahadasha: {current.get('mahadasha', 'N/A')} (ends: {current.get('mahadasha_end', 'N/A')})\n"
            f"Antardasha: {current.get('antardasha', 'N/A')} (ends: {antardasha_end})"
        )

        transit_raw = structured_data.get("transits", {})
        transits_list = transit_raw.get("data", {}).get("transits", [])
        transits_str = (
            json.dumps(transits_list, indent=2) if transits_list else "Not available"
        )

        return template.format(
            d1_data=d1_str,
            d9_data=d9_str,
            d30_data=d30_str,
            dasha=dasha_str,
            transits=transits_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Darakaraka
    # Placeholders: planet_degrees, d9_data
    # -------------------------------------------------------------------------
    @classmethod
    def _build_darakaraka_prompt(cls, template: str, structured_data: dict) -> str:
        import json

        planet_map = cls._get_d1_planet_map(structured_data)

        # Format planet degrees (excluding Ascendant, Rahu, Ketu for DK)
        degree_lines = []
        for name, data in planet_map.items():
            if name not in ("Ascendant", "Rahu", "Ketu"):
                degree_lines.append(
                    f"  {name}: {data.get('degree', 'N/A')}° in {data.get('sign', 'N/A')}"
                )
        planet_degrees = "\n".join(degree_lines) if degree_lines else "Not available"

        # Extract D9 chart
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break
        d9_str = json.dumps(d9_positions, indent=2)

        transit_raw = structured_data.get("transits", {})
        transits_list = transit_raw.get("data", {}).get("transits", [])
        transits_str = (
            json.dumps(transits_list, indent=2) if transits_list else "Not available"
        )

        return template.format(
            planet_degrees=planet_degrees,
            d9_data=d9_str,
            transits=transits_str,
        )
