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
        name = profile.display_name
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
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=45)
        except requests.RequestException as e:
            raise AstrologyAPIError(f"Network error calling {endpoint}: {e}")

        if not resp.ok:
            error_data = resp.text
            import logging

            view_logger = logging.getLogger("astrology.views")
            view_logger.error(f"Astrology API error [{resp.status_code}]: {error_data}")
            raise AstrologyAPIError(
                f"Astrology API error [{resp.status_code}]",
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
        Returns all 16 divisional charts for advanced calculations.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "charts": ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"],
        }
        return self._post("divisional-chart", payload)

    def get_transit(self, profile, transit_date: str = None) -> dict:
        """
        Calls POST /vedic/transit.
        Returns planetary transits relative to the natal Moon for a specific date (or today).
        """
        payload = {
            "subject": self._subject_payload(profile),
            "options": {"language": "en"},
        }
        if transit_date:
            payload["transit_date"] = transit_date
        return self._post("transit", payload)

    def get_nakshatra_predictions(self, profile) -> dict:
        """
        Calls POST /vedic/nakshatra-predictions.
        Returns daily predictions based on the current Moon's transit over
        the natal Nakshatra, including Tara Bala analysis.
        """
        payload = {
            "subject": self._subject_payload(profile),
            "options": {"language": "en"},
        }
        return self._post("nakshatra-predictions", payload)

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
        BENEFIC_PLANETS_PROMPT,
        MALEFIC_PLANETS_PROMPT,
        CHART_ANALYSIS_PROMPT,
        PLANETARY_STATES_PROMPT,
        ASTRO_ENERGY_PROMPT,
        RASHI_PLANETS_PROMPT,
        LAGNA_LORD_PROMPT,
        CHALLENGES_PROMPT,
        DAILY_TARA_PROMPT,
        FOREIGN_TRAVEL_PROMPT,
        D2_HORA_PROMPT,
        D4_CHATURTHAMSHA_PROMPT,
        D10_DASHAMSHA_PROMPT,
        D7_SAPTAMSHA_PROMPT,
        D12_DWADASHAMSHA_PROMPT,
        D60_SHASHTIAMSHA_PROMPT,
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
        "benefic_planets": BENEFIC_PLANETS_PROMPT,
        "malefic_planets": MALEFIC_PLANETS_PROMPT,
        "chart_analysis": CHART_ANALYSIS_PROMPT,
        "planetary_states": PLANETARY_STATES_PROMPT,
        "astro_energy": ASTRO_ENERGY_PROMPT,
        "rashi_planets": RASHI_PLANETS_PROMPT,
        "lagna_lord": LAGNA_LORD_PROMPT,
        "challenges": CHALLENGES_PROMPT,
        "daily_tara": DAILY_TARA_PROMPT,
        "foreign_travel": FOREIGN_TRAVEL_PROMPT,
        "d2_hora": D2_HORA_PROMPT,
        "d4_chaturthamsha": D4_CHATURTHAMSHA_PROMPT,
        "d10_dashamsha": D10_DASHAMSHA_PROMPT,
        "d7_saptamsha": D7_SAPTAMSHA_PROMPT,
        "d12_dwadashamsha": D12_DWADASHAMSHA_PROMPT,
        "d60_shashtiamsha": D60_SHASHTIAMSHA_PROMPT,
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

        # Extract custom user prompt from Admin if available
        config = AIPromptConfiguration.objects.filter(
            category=category, is_active=True
        ).first()
        user_prompt_text = ""
        if config and config.user_prompt.strip():
            user_prompt_text = f"USER PRIORITY FOCUS:\n{config.user_prompt.strip()}\n"

        # Categories with specific named placeholders are handled differently.
        if category == "mental_health":
            prompt = cls._build_mental_health_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "btr":
            prompt = cls._build_btr_prompt(
                prompt_template,
                structured_data,
                extra_context or {},
                user_prompt=user_prompt_text,
            )
        elif category == "marriage":
            prompt = cls._build_marriage_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "prosperity_sav":
            prompt = cls._build_sav_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "parasari":
            prompt = cls._build_parasari_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "navatara":
            prompt = cls._build_navatara_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "medical":
            prompt = cls._build_medical_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "darakaraka":
            prompt = cls._build_darakaraka_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "benefic_planets":
            prompt = cls._build_benefic_planets_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "malefic_planets":
            prompt = cls._build_malefic_planets_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "chart_analysis":
            prompt = cls._build_chart_analysis_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "planetary_states":
            prompt = cls._build_planetary_states_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "lagna_lord":
            prompt = cls._build_lagna_lord_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "rashi_planets":
            prompt = cls._build_rashi_planets_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "challenges":
            prompt = cls._build_challenges_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "astro_energy":
            prompt = cls._build_astro_energy_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "foreign_travel":
            prompt = cls._build_foreign_travel_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d2_hora":
            prompt = cls._build_d2_hora_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d4_chaturthamsha":
            prompt = cls._build_d4_chaturthamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d10_dashamsha":
            prompt = cls._build_d10_dashamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d7_saptamsha":
            prompt = cls._build_d7_saptamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d12_dwadashamsha":
            prompt = cls._build_d12_dwadashamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d60_shashtiamsha":
            prompt = cls._build_d60_shashtiamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        else:
            # All other prompts use a single {astrology_data} JSON dump
            data_str = json.dumps(structured_data, indent=2)
            prompt = prompt_template.format(
                astrology_data=data_str, user_prompt=user_prompt_text
            )

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            raise GeminiAIError(f"Failed to generate insight from Gemini: {str(e)}")

    @classmethod
    def chat_about_insight(
        cls,
        category: str,
        structured_data: dict,
        insight_text: str,
        history: list,
        new_message: str,
    ) -> str:
        import json
        from google import genai
        from google.genai import types

        if category == "divisional-charts":
            context_data = (
                structured_data.get("divisional_data", {})
                .get("data", {})
                .get("charts", [])
            )
            system_prompt = f"""You are an expert Vedic astrologer. The user is asking about their Divisional Charts (Vargas).
Here is their complete set of 16 divisional charts data (including D1 Lagna, D9 Navamsa, D10 Dasamsa, D60 Shastiamsa, etc.): {json.dumps(context_data, indent=2)}

You can answer questions about any of the 16 divisional charts. Identify which chart(s) they are asking about (e.g. D1, D9, D10, D60) and analyze their planetary placements, signs, and houses based on this data."""
        elif category == "dasha":
            dasha_data = structured_data.get("dasha", {})
            system_prompt = f"""You are an expert Vedic astrologer. The user is asking about their Vimshottari Dasha timing sequences (Mahadashas, Antardashas, and divisions).
Here is their complete Vimshottari Dasha timing schedule: {json.dumps(dasha_data, indent=2)}"""
        elif category == "navatara":
            tara_data = structured_data.get("daily_tara_bala", {})
            system_prompt = f"""You are an expert Vedic astrologer. The user is asking about their current Navatara (Daily Tara Bala).
Here is today's Navatara data and AI guidance: {json.dumps(tara_data, indent=2)}

You also have their general Navatara life insight:
{insight_text or "Not available"}"""
        else:
            system_prompt = f"""You are an expert Vedic astrologer assistant specializing in the "{category}" category.

You have been given the following pre-generated astrological insight for this person:
--- INSIGHT START ---
{insight_text or "Not available"}
--- INSIGHT END ---"""

        system_prompt += f"""

You also have their complete birth and natal table data for reference:
--- DATA START ---
{json.dumps(structured_data, indent=2)}
--- DATA END ---

Your role is to answer follow-up questions and provide deeper clarification.

STRICT RULES:
1. ONLY answer questions directly related to the {category} topic and this user's specific birth chart or insight text.
2. Ground ALL answers in the provided insight text and birth data. Do NOT fabricate or guess planetary positions.
3. If the user asks something unrelated to astrology, this specific category, or their own chart, politely decline to answer.
4. Keep answers concise, warm, insightful, and clear.
"""

        contents = []
        for msg in history:
            # Assume msg is dict with 'role' ('user' or 'model') and 'content'
            contents.append(
                types.Content(
                    role=msg["role"], parts=[types.Part.from_text(text=msg["content"])]
                )
            )

        # Append the latest user message
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=new_message)])
        )

        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.3,
                ),
            )
            return response.text
        except Exception as e:
            raise GeminiAIError(f"Failed to generate chat response: {str(e)}")

    @staticmethod
    def _build_mental_health_prompt(
        template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
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
            user_prompt=user_prompt,
            lagna=lagna_str,
            moon=moon_str,
            mercury=mercury_str,
            house4=house4_str,
        )

    @staticmethod
    def _build_btr_prompt(
        template: str, structured_data: dict, extra_context: dict, user_prompt: str = ""
    ) -> str:
        """
        Uses the extra_context dictionary for user-provided life event dates,
        and injects the kp_system JSON data as {astrology_data}.
        """
        import json

        kp_data_str = json.dumps(structured_data.get("kp_system", {}), indent=2)

        return template.format(
            user_prompt=user_prompt,
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
    # Builder: Marriage Analysis (Comprehensive)
    # Placeholders: name, gender, date_of_birth, time_of_birth, place_of_birth,
    #   birth_time_note, marital_status, personal_context, lagna,
    #   d1_house_lords, d1_planets, d9_lagna, d9_house_lords, d9_planets,
    #   mahadasha, antardasha, dasha_sequence, transits
    # -------------------------------------------------------------------------
    @classmethod
    def _build_marriage_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        # --- Profile context (personal & birth details) ---
        ctx = structured_data.get("profile_context", {})
        name = ctx.get("name") or "Not provided"
        gender = ctx.get("gender") or "Not specified"
        birth_year = ctx.get("birth_year", "?")
        birth_month = ctx.get("birth_month", "?")
        birth_day = ctx.get("birth_day", "?")
        birth_hour = ctx.get("birth_hour", "?")
        birth_minute = ctx.get("birth_minute", "?")
        city = ctx.get("city", "?")
        country_code = ctx.get("country_code", "?")
        marriage_date = ctx.get("marriage_date")
        kids = ctx.get("kids")
        comments = ctx.get("comments")

        date_of_birth = (
            f"{birth_year}-{str(birth_month).zfill(2)}-{str(birth_day).zfill(2)}"
        )
        time_of_birth = f"{str(birth_hour).zfill(2)}:{str(birth_minute).zfill(2)}"
        place_of_birth = f"{city}, {country_code}"
        birth_time_note = (
            "Birth time fields are provided by the user. "
            "Assumed accurate unless stated otherwise."
        )

        # Derive marital status
        if marriage_date:
            marital_status = f"Married (marriage date on record: {marriage_date})"
        elif kids:
            marital_status = (
                f"Likely married or in committed relationship (has {kids} child/children)"
            )
        else:
            marital_status = "Unknown / Not specified"

        # Personal context block
        ctx_parts = []
        if marriage_date:
            ctx_parts.append(f"Marriage Date: {marriage_date}")
        if kids is not None:
            ctx_parts.append(f"Number of Children: {kids}")
        if comments:
            ctx_parts.append(f"Additional Notes: {comments}")
        personal_context = (
            "\n".join(ctx_parts) if ctx_parts else "No additional context provided."
        )

        # --- Lagna + sign order helper ---
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        # --- D1 house lords (all 12) ---
        birth_planets = cls._get_birth_planets(structured_data)
        bp_map = {p.get("planet"): p for p in birth_planets}

        # Build house → [planets] map for conjunction detection
        h_to_planets: dict = {}
        for p in birth_planets:
            h = p.get("house")
            if h:
                h_to_planets.setdefault(h, []).append(p.get("planet"))

        d1_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = bp_map.get(lord_name, {})
            lord_house = lord_data.get("house", "N/A")
            lord_sign = lord_data.get("sign", "N/A")
            lord_dignity = lord_data.get("dignity", "N/A")
            d1_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | Placed in House {lord_house} ({lord_sign})"
                f" | Dignity: {lord_dignity}"
            )
        d1_house_lords_str = "\n".join(d1_house_lord_lines)

        # --- Full D1 planetary data ---
        d1_lines = []
        for p in birth_planets:
            pname = p.get("planet", "")
            house = p.get("house")
            conditions = []
            if p.get("is_retrograde") == "Yes":
                conditions.append("Retrograde")
            if p.get("is_combust") == "Yes":
                conditions.append("Combust")
            cond_str = ", ".join(conditions) if conditions else "Direct/Normal"
            conjuncts = [
                x for x in h_to_planets.get(house, []) if x != pname
            ]
            conj_str = ", ".join(conjuncts) if conjuncts else "None"
            d1_lines.append(
                f"  {pname} → House: {house}"
                f" | Sign: {p.get('sign', 'N/A')}"
                f" | Degree: {p.get('degree', 'N/A')}°"
                f" | Nakshatra: {p.get('nakshatra', 'N/A')}"
                f" | Dignity: {p.get('dignity', 'N/A')}"
                f" | Conditions: {cond_str}"
                f" | Conjunct: {conj_str}"
            )
        d1_planets_str = "\n".join(d1_lines) if d1_lines else "Not available"

        # --- D9 data ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break

        # D9 Lagna
        d9_asc = next(
            (p for p in d9_positions if p.get("planet") == "Ascendant"), {}
        )
        d9_lagna_sign = d9_asc.get("sign", "N/A")
        d9_lagna_lord = _sign_lords.get(d9_lagna_sign, "N/A")
        d9_lagna_str = f"{d9_lagna_sign} (Lord: {d9_lagna_lord})"

        # D9 house lords — derived from D9 ascendant
        d9_planet_map = {p.get("planet"): p for p in d9_positions}
        d9_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d9_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d9_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            # Calculate D9 house for this lord from its sign + D9 lagna
            try:
                d9_lagna_idx = cls._SIGN_ORDER.index(d9_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d9_house = ((lord_sign_idx - d9_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d9_house = "N/A"
            d9_house_lord_lines.append(
                f"  D9 House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D9 House {lord_d9_house} ({lord_sign})"
            )
        d9_house_lords_str = "\n".join(d9_house_lord_lines)

        # D9 planetary positions with calculated house numbers
        d9_planet_lines = []
        for p in d9_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            try:
                d9_lagna_idx = cls._SIGN_ORDER.index(d9_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d9_house_num = ((p_sign_idx - d9_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d9_house_num = "N/A"
            d9_planet_lines.append(
                f"  {pname} → D9 House: {d9_house_num}"
                f" | Sign: {p_sign}"
                f" | Degree: {p.get('degree', 'N/A')}°"
            )
        d9_planets_str = (
            "\n".join(d9_planet_lines) if d9_planet_lines else "Not available"
        )

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )

        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        # --- Transits ---
        transit_raw = structured_data.get("transits", {})
        transits_list = transit_raw.get("data", {}).get("transits", [])
        transits_str = (
            json.dumps(transits_list, indent=2) if transits_list else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            name=name,
            gender=gender,
            date_of_birth=date_of_birth,
            time_of_birth=time_of_birth,
            place_of_birth=place_of_birth,
            birth_time_note=birth_time_note,
            marital_status=marital_status,
            personal_context=personal_context,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            d1_house_lords=d1_house_lords_str,
            d1_planets=d1_planets_str,
            d9_lagna=d9_lagna_str,
            d9_house_lords=d9_house_lords_str,
            d9_planets=d9_planets_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
            transits=transits_str,
        )

    # -------------------------------------------------------------------------
    # Builder: SAV Prosperity
    # Placeholders: lagna, sav_house_points, saturn_house
    # -------------------------------------------------------------------------
    @classmethod
    def _build_sav_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
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
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            sav_house_points=sav_house_points,
            saturn_house=saturn_house,
        )

    # -------------------------------------------------------------------------
    # Builder: Parasari Relationships
    # Placeholders: lagna, sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu
    # -------------------------------------------------------------------------
    @classmethod
    def _build_parasari_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
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
            user_prompt=user_prompt,
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
    def _build_navatara_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
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
            user_prompt=user_prompt,
            nakshatra=birth_nakshatra,
            pada="Not provided",
        )

    # -------------------------------------------------------------------------
    # Builder: Medical Astrology
    # Placeholders: d1_data, d9_data, d30_data, dasha
    # -------------------------------------------------------------------------
    @classmethod
    def _build_medical_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
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
            user_prompt=user_prompt,
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
    def _build_darakaraka_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
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
            user_prompt=user_prompt,
            planet_degrees=planet_degrees,
            d9_data=d9_str,
            transits=transits_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Benefic Planets
    # Placeholders: lagna, planets, d9_data, dasha
    # -------------------------------------------------------------------------
    @classmethod
    def _build_benefic_planets_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        birth_planets = cls._get_birth_planets(structured_data)
        planet_lines = []
        for p in birth_planets:
            planet_lines.append(
                f"  {p.get('planet')} - {p.get('sign')} - House {p.get('house')}"
            )
        planets_str = "\n".join(planet_lines) if planet_lines else "Not available"

        # Extract D9 chart
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break
        d9_str = json.dumps(d9_positions, indent=2)

        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        antardasha_end = current.get("antardasha_end", "N/A")
        dasha_str = (
            f"Mahadasha: {current.get('mahadasha', 'N/A')} (ends: {current.get('mahadasha_end', 'N/A')})\n"
            f"Antardasha: {current.get('antardasha', 'N/A')} (ends: {antardasha_end})"
        )

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            planets=planets_str,
            d9_data=d9_str,
            dasha=dasha_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Malefic Planets
    # Placeholders: lagna, planets, d9_data, dasha
    # -------------------------------------------------------------------------
    @classmethod
    def _build_malefic_planets_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        birth_planets = cls._get_birth_planets(structured_data)
        planet_lines = []
        for p in birth_planets:
            planet_lines.append(
                f"  {p.get('planet')} - {p.get('sign')} - House {p.get('house')}"
            )
        planets_str = "\n".join(planet_lines) if planet_lines else "Not available"

        # Extract D9 chart
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break
        d9_str = json.dumps(d9_positions, indent=2)

        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        antardasha_end = current.get("antardasha_end", "N/A")
        dasha_str = (
            f"Mahadasha: {current.get('mahadasha', 'N/A')} (ends: {current.get('mahadasha_end', 'N/A')})\n"
            f"Antardasha: {current.get('antardasha', 'N/A')} (ends: {antardasha_end})"
        )

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            planets=planets_str,
            d9_data=d9_str,
            dasha=dasha_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Chart Analysis
    # Placeholders: lagna, d1_data, d9_data, dasha
    # -------------------------------------------------------------------------
    @classmethod
    def _build_chart_analysis_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        birth_planets = cls._get_birth_planets(structured_data)
        d1_str = (
            json.dumps(birth_planets, indent=2) if birth_planets else "Not available"
        )

        # Extract D9 chart
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break
        d9_str = json.dumps(d9_positions, indent=2)

        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        antardasha_end = current.get("antardasha_end", "N/A")
        dasha_str = (
            f"Mahadasha: {current.get('mahadasha', 'N/A')} (ends: {current.get('mahadasha_end', 'N/A')})\n"
            f"Antardasha: {current.get('antardasha', 'N/A')} (ends: {antardasha_end})"
        )

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            d1_data=d1_str,
            d9_data=d9_str,
            dasha=dasha_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Planetary States
    # Placeholders: astrology_data (D1), d9_data
    # -------------------------------------------------------------------------
    @classmethod
    def _build_planetary_states_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        birth_planets = cls._get_birth_planets(structured_data)
        d1_str = (
            json.dumps(birth_planets, indent=2) if birth_planets else "Not available"
        )

        # Extract D9 chart
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break
        d9_str = json.dumps(d9_positions, indent=2)

        return template.format(
            user_prompt=user_prompt,
            astrology_data=d1_str,
            d9_data=d9_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Lagna Lord Position
    # Placeholders: lagna, lagna_lord, d1_sign, d1_house, d9_sign, d9_house,
    #               degrees, condition
    # -------------------------------------------------------------------------
    @classmethod
    def _build_lagna_lord_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord_name = asc.get("lord", "N/A")

        # Find Lagna Lord in D1
        birth_planets = cls._get_birth_planets(structured_data)
        ll_d1 = next(
            (p for p in birth_planets if p.get("planet") == lagna_lord_name), {}
        )

        # Extract D9 chart to find Lagna Lord there
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break

        ll_d9 = next(
            (p for p in d9_positions if p.get("planet") == lagna_lord_name), {}
        )

        condition_parts = []
        if ll_d1.get("is_combust") == "Yes":
            condition_parts.append("Combust")
        if ll_d1.get("is_retrograde") == "Yes":
            condition_parts.append("Retrograde")
        condition_str = ", ".join(condition_parts) if condition_parts else "Normal"

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord_name})",
            lagna_lord=lagna_lord_name,
            d1_sign=ll_d1.get("sign", "N/A"),
            d1_house=ll_d1.get("house", "N/A"),
            d9_sign=ll_d9.get("sign", "N/A"),
            d9_house=ll_d9.get("house", "N/A"),
            degrees=ll_d1.get("degree", "N/A"),
            condition=condition_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Meaning of Rashi Planets
    # Placeholders: lagna, h1-h12, placements
    # -------------------------------------------------------------------------
    @classmethod
    def _build_rashi_planets_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        sign_lords = {
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

        # Dynamically find lord for each house
        house_lords = {}
        for h in range(1, 13):
            h_sign = cls._sign_of_house(lagna_sign, h - 1)
            lord_name = sign_lords.get(h_sign, "N/A")
            # We need to find the house for this planet in D1
            birth_planets = cls._get_birth_planets(structured_data)
            p_data = next(
                (p for p in birth_planets if p.get("planet") == lord_name), {}
            )
            lord_house = p_data.get("house", "N/A")
            lord_sign = p_data.get("sign", "N/A")

            house_lords[f"h{h}"] = f"{lord_name} in House {lord_house} ({lord_sign})"

        placements_data = cls._get_birth_planets(structured_data)
        placements_str = json.dumps(placements_data, indent=2)

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            placements=placements_str,
            **house_lords,
        )

    # -------------------------------------------------------------------------
    # Builder: Challenges and Learning
    # Placeholders: lagna, planets, d9_data
    # -------------------------------------------------------------------------
    @classmethod
    def _build_challenges_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        birth_planets = cls._get_birth_planets(structured_data)
        planet_lines = []
        for p in birth_planets:
            planet_lines.append(
                f"  {p.get('planet')} - Sign: {p.get('sign')} - House: {p.get('house')}"
            )
        planets_str = "\n".join(planet_lines)

        # Extract D9 chart
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d9_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D9":
                d9_positions = chart.get("positions", [])
                break
        d9_str = json.dumps(d9_positions, indent=2)

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            planets=planets_str,
            d9_data=d9_str,
        )

    # -------------------------------------------------------------------------
    # Builder: 12-Dimensional Astro Energy
    # Placeholders: lagna, planets
    # -------------------------------------------------------------------------
    @classmethod
    def _build_astro_energy_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        birth_planets = cls._get_birth_planets(structured_data)
        planet_lines = []
        for p in birth_planets:
            planet_lines.append(
                f"  {p.get('planet')} (House {p.get('house')}, {p.get('sign')})"
            )
        planets_str = "\n".join(planet_lines)

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            planets=planets_str,
        )

    # -------------------------------------------------------------------------
    # Builder: Foreign Travel & Settlement
    # Placeholders: lagna, house_lords, d1_data, d9_data, d4_data, d10_data,
    #               d24_data, dasha, dasha_sequence, transits
    # -------------------------------------------------------------------------
    @classmethod
    def _build_foreign_travel_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        import json

        # --- Lagna + lord ---
        planet_map = cls._get_d1_planet_map(structured_data)
        asc = planet_map.get("Ascendant", {})
        lagna_sign = asc.get("sign", "N/A")
        lagna_lord = asc.get("lord", "N/A")

        # --- House lords: for each house, find the ruling planet and where it sits ---
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }
        birth_planets = cls._get_birth_planets(structured_data)
        bp_map = {p.get("planet"): p for p in birth_planets}

        house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = bp_map.get(lord_name, {})
            lord_house = lord_data.get("house", "N/A")
            lord_sign = lord_data.get("sign", "N/A")
            lord_dignity = lord_data.get("dignity", "N/A")
            house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | Placed in House {lord_house} ({lord_sign})"
                f" | Dignity: {lord_dignity}"
            )
        house_lords_str = "\n".join(house_lord_lines)

        # --- Full D1 planet data (sign, house, degree, dignity, retrograde, combust) ---
        d1_lines = []
        for p in birth_planets:
            conditions = []
            if p.get("is_retrograde") == "Yes":
                conditions.append("Retrograde")
            if p.get("is_combust") == "Yes":
                conditions.append("Combust")
            cond_str = ", ".join(conditions) if conditions else "Direct/Normal"
            d1_lines.append(
                f"  {p.get('planet')} → Sign: {p.get('sign', 'N/A')}"
                f" | House: {p.get('house', 'N/A')}"
                f" | Degree: {p.get('degree', 'N/A')}°"
                f" | Dignity: {p.get('dignity', 'N/A')}"
                f" | Nakshatra: {p.get('nakshatra', 'N/A')}"
                f" | Conditions: {cond_str}"
            )
        d1_data_str = "\n".join(d1_lines) if d1_lines else "Not available"

        # --- Extract D4, D9, D10, D24 from divisional_data ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        charts_by_code = {c.get("chart"): c.get("positions", []) for c in all_charts}

        d9_str = json.dumps(charts_by_code.get("D9", []), indent=2)
        d4_str = json.dumps(charts_by_code.get("D4", []), indent=2)
        d10_str = json.dumps(charts_by_code.get("D10", []), indent=2)
        d24_str = json.dumps(charts_by_code.get("D24", []), indent=2)

        # --- Dasha: current period + upcoming antardasha sequence ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        dasha_str = (
            f"Mahadasha: {current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})\n"
            f"Antardasha: {current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )

        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"

        # --- Today's transits ---
        transit_raw = structured_data.get("transits", {})
        transits_list = transit_raw.get("data", {}).get("transits", [])
        transits_str = (
            json.dumps(transits_list, indent=2) if transits_list else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            lagna=f"{lagna_sign} (Lord: {lagna_lord})",
            house_lords=house_lords_str,
            d1_data=d1_data_str,
            d9_data=d9_str,
            d4_data=d4_str,
            d10_data=d10_str,
            d24_data=d24_str,
            dasha=dasha_str,
            dasha_sequence=dasha_sequence_str,
            transits=transits_str,
        )

    # -------------------------------------------------------------------------
    # Builder: D2 Hora Chart Analysis
    # Placeholders: birth_time_note, hora_method_note, d2_lagna, d2_house_lords,
    #   d2_planets, hora_balance, d1_cross_ref, mahadasha, antardasha,
    #   dasha_sequence, user_prompt
    # -------------------------------------------------------------------------
    @classmethod
    def _build_d2_hora_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        # Hora type: Parashari D2 uses only Leo (Sun Hora) and Cancer (Moon Hora)
        def hora_type(sign: str) -> str:
            if sign == "Leo":
                return "Sun Hora"
            elif sign in ("Can", "Cancer"):
                return "Moon Hora"
            else:
                return f"Extended ({sign})"

        birth_time_note = (
            "Birth time provided by user. D2 divisional charts require accurate birth "
            "time — if birth time is approximate or unknown, D2 positions may shift."
        )
        hora_method_note = (
            "Parashari Hora (traditional): planets fall in Leo (Sun Hora) for "
            "self-earned wealth / authority, or Cancer (Moon Hora) for family support / "
            "liquidity / public income. If your software uses an extended Hora method "
            "(Jagannatha etc.), planet signs will differ."
        )

        # --- Extract D2 positions ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d2_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D2":
                d2_positions = chart.get("positions", [])
                break

        # D2 Lagna
        d2_asc = next(
            (p for p in d2_positions if p.get("planet") == "Ascendant"), {}
        )
        d2_lagna_sign = d2_asc.get("sign", "N/A")
        d2_lagna_lord = _sign_lords.get(d2_lagna_sign, "N/A")
        d2_lagna_str = (
            f"{d2_lagna_sign} (Lord: {d2_lagna_lord})"
            f" | {hora_type(d2_lagna_sign)}"
        )

        # D2 house lords (all 12) — derived from D2 ascendant
        d2_planet_map = {p.get("planet"): p for p in d2_positions}
        d2_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d2_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d2_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            try:
                d2_lagna_idx = cls._SIGN_ORDER.index(d2_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d2_house = ((lord_sign_idx - d2_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d2_house = "N/A"
            d2_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D2 House {lord_d2_house} ({lord_sign})"
                f" | {hora_type(lord_sign)}"
            )
        d2_house_lords_str = "\n".join(d2_house_lord_lines)

        # D2 planetary placements with hora type
        sun_hora_count = 0
        moon_hora_count = 0
        other_hora_count = 0
        d2_planet_lines = []
        for p in d2_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            p_hora = hora_type(p_sign)
            # house in D2
            try:
                d2_lagna_idx = cls._SIGN_ORDER.index(d2_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d2_house_num = ((p_sign_idx - d2_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d2_house_num = "N/A"
            d2_planet_lines.append(
                f"  {pname} → D2 House: {d2_house_num}"
                f" | Sign: {p_sign}"
                f" | Degree: {p.get('degree', 'N/A')}°"
                f" | Hora: {p_hora}"
            )
            if p_hora == "Sun Hora":
                sun_hora_count += 1
            elif p_hora == "Moon Hora":
                moon_hora_count += 1
            else:
                other_hora_count += 1

        d2_planets_str = "\n".join(d2_planet_lines) if d2_planet_lines else "Not available"

        # Hora balance summary
        hora_balance_str = (
            f"  Sun Hora planets: {sun_hora_count} (self-earned wealth, authority, independence)\n"
            f"  Moon Hora planets: {moon_hora_count} (family support, liquidity, public income)\n"
        )
        if other_hora_count:
            hora_balance_str += (
                f"  Extended Hora (non-Leo/Cancer): {other_hora_count} planets "
                f"(Jagannatha or alternate D2 method in use)\n"
            )
        if sun_hora_count > moon_hora_count:
            hora_balance_str += "  Dominant theme: Self-driven / authority-based wealth"
        elif moon_hora_count > sun_hora_count:
            hora_balance_str += "  Dominant theme: Family-supported / liquid / public-facing wealth"
        else:
            hora_balance_str += "  Balance: Mixed self-earned and family/public wealth"

        # --- D1 cross-reference ---
        birth_planets = cls._get_birth_planets(structured_data)
        planet_map = cls._get_d1_planet_map(structured_data)
        d1_asc = planet_map.get("Ascendant", {})
        d1_lagna_sign = d1_asc.get("sign", "N/A")
        d1_lagna_lord = d1_asc.get("lord", "N/A")

        bp_map = {p.get("planet"): p for p in birth_planets}

        def _d1_lord_of_house(h: int) -> str:
            h_sign = cls._sign_of_house(d1_lagna_sign, h)
            return _sign_lords.get(h_sign, "N/A")

        d1_2nd_lord = _d1_lord_of_house(2)
        d1_11th_lord = _d1_lord_of_house(11)

        def _planet_summary(planet_name: str) -> str:
            p = bp_map.get(planet_name, {})
            return (
                f"House {p.get('house', 'N/A')}"
                f" | Sign: {p.get('sign', 'N/A')}"
                f" | Dignity: {p.get('dignity', 'N/A')}"
            )

        d1_cross_ref_str = (
            f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
            f"  D1 2nd Lord: {d1_2nd_lord} — {_planet_summary(d1_2nd_lord)}\n"
            f"  D1 11th Lord: {d1_11th_lord} — {_planet_summary(d1_11th_lord)}\n"
            f"  D1 Jupiter — {_planet_summary('Jupiter')}\n"
            f"  D1 Venus  — {_planet_summary('Venus')}\n"
            f"  D1 Mercury — {_planet_summary('Mercury')}"
        )

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )
        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            birth_time_note=birth_time_note,
            hora_method_note=hora_method_note,
            d2_lagna=d2_lagna_str,
            d2_house_lords=d2_house_lords_str,
            d2_planets=d2_planets_str,
            hora_balance=hora_balance_str,
            d1_cross_ref=d1_cross_ref_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
        )

    # -------------------------------------------------------------------------
    # Builder: D4 Chaturthamsha Chart Analysis
    # Placeholders: birth_time_note, d4_lagna, d4_house_lords, d4_planets,
    #   d4_divisions_summary, d1_cross_ref, mahadasha, antardasha,
    #   dasha_sequence, user_prompt
    # -------------------------------------------------------------------------
    @classmethod
    def _build_d4_chaturthamsha_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        def parse_degree(deg_val) -> float:
            if isinstance(deg_val, (int, float)):
                return float(deg_val)
            try:
                if isinstance(deg_val, str) and ":" in deg_val:
                    parts = deg_val.split(":")
                    deg = float(parts[0])
                    min_val = float(parts[1]) if len(parts) > 1 else 0.0
                    sec_val = float(parts[2]) if len(parts) > 2 else 0.0
                    return deg + (min_val / 60.0) + (sec_val / 3600.0)
                return float(deg_val)
            except Exception:
                return 0.0

        def get_d4_division(deg_str_or_num) -> str:
            d = parse_degree(deg_str_or_num)
            d = d % 30.0
            if d < 7.5:
                return "Sanaki (0°00′ to 7°30′: Active effort, pursuit of happiness)"
            elif d < 15.0:
                return "Sanand (7°30′ to 15°00′: Acceptance, inner contentment)"
            elif d < 22.5:
                return "Sanat_Kumar (15°00′ to 22°30′: Youthful, adaptive happiness)"
            else:
                return "Sanatan (22°30′ to 30°00′: Stable, eternal, mature happiness)"

        birth_time_note = (
            "Birth time provided by user. D4 divisional charts require accurate birth "
            "time — if birth time is approximate or unknown, D4 positions may shift."
        )

        # --- Extract D4 positions ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d4_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D4":
                d4_positions = chart.get("positions", [])
                break

        planet_map = cls._get_d1_planet_map(structured_data)

        # D4 Lagna
        d4_asc = next(
            (p for p in d4_positions if p.get("planet") == "Ascendant"), {}
        )
        d4_lagna_sign = d4_asc.get("sign", "N/A")
        d4_lagna_lord = _sign_lords.get(d4_lagna_sign, "N/A")
        
        # Lagna division based on D1 Ascendant degree
        d1_asc = planet_map.get("Ascendant", {})
        d1_asc_deg = d1_asc.get("degree", 0.0)
        d4_lagna_division = get_d4_division(d1_asc_deg)
        d4_lagna_str = f"{d4_lagna_sign} (Lord: {d4_lagna_lord}) | Division: {d4_lagna_division}"

        # D4 house lords (all 12)
        d4_planet_map = {p.get("planet"): p for p in d4_positions}
        d4_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d4_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d4_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            try:
                d4_lagna_idx = cls._SIGN_ORDER.index(d4_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d4_house = ((lord_sign_idx - d4_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d4_house = "N/A"
            
            # Get lord D1 degree to calculate its division
            lord_d1_data = planet_map.get(lord_name, {})
            lord_d1_deg = lord_d1_data.get("degree", 0.0)
            lord_division = get_d4_division(lord_d1_deg)
            
            d4_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D4 House {lord_d4_house} ({lord_sign})"
                f" | Division: {lord_division}"
            )
        d4_house_lords_str = "\n".join(d4_house_lord_lines)

        # D4 planetary placements
        d4_planet_lines = []
        divisions_count = {"Sanaki": 0, "Sanand": 0, "Sanat_Kumar": 0, "Sanatan": 0}
        for p in d4_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            try:
                d4_lagna_idx = cls._SIGN_ORDER.index(d4_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d4_house_num = ((p_sign_idx - d4_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d4_house_num = "N/A"
            
            p_dignity = p.get("dignity", "N/A")
            
            # Division based on D1 degree
            p_d1_data = planet_map.get(pname, {})
            p_d1_deg = p_d1_data.get("degree", 0.0)
            p_division = get_d4_division(p_d1_deg)
            
            div_key = p_division.split(" (")[0]
            if div_key in divisions_count:
                divisions_count[div_key] += 1
                
            d4_planet_lines.append(
                f"  {pname} → D4 House: {d4_house_num}"
                f" | Sign: {p_sign}"
                f" | D4 Degree: {p.get('degree', 'N/A')}°"
                f" | Dignity: {p_dignity}"
                f" | D4 Division: {p_division}"
            )
        d4_planets_str = "\n".join(d4_planet_lines) if d4_planet_lines else "Not available"

        # D4 divisions summary
        d4_divisions_summary_str = (
            f"  Sanaki planets: {divisions_count['Sanaki']} (desire for comfort, active effort)\n"
            f"  Sanand planets: {divisions_count['Sanand']} (inner contentment, emotional steadiness)\n"
            f"  Sanat_Kumar planets: {divisions_count['Sanat_Kumar']} (adaptive happiness, changing life stages)\n"
            f"  Sanatan planets: {divisions_count['Sanatan']} (eternal / mature happiness, stable inner peace)\n"
        )

        # --- D1 cross-reference ---
        birth_planets = cls._get_birth_planets(structured_data)
        d1_asc = planet_map.get("Ascendant", {})
        d1_lagna_sign = d1_asc.get("sign", "N/A")
        d1_lagna_lord = d1_asc.get("lord", "N/A")
        bp_map = {p.get("planet"): p for p in birth_planets}

        def _d1_lord_of_house(h: int) -> str:
            h_sign = cls._sign_of_house(d1_lagna_sign, h)
            return _sign_lords.get(h_sign, "N/A")

        d1_4th_lord = _d1_lord_of_house(4)

        def _planet_summary(planet_name: str) -> str:
            p = bp_map.get(planet_name, {})
            return (
                f"House {p.get('house', 'N/A')}"
                f" | Sign: {p.get('sign', 'N/A')}"
                f" | Dignity: {p.get('dignity', 'N/A')}"
            )

        d1_cross_ref_str = (
            f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
            f"  D1 4th House Lord: {d1_4th_lord} — {_planet_summary(d1_4th_lord)}\n"
            f"  D1 Moon — {_planet_summary('Moon')}\n"
            f"  D1 Mars (Significator of Land/Property) — {_planet_summary('Mars')}\n"
            f"  D1 Venus (Significator of Vehicles/Comforts) — {_planet_summary('Venus')}"
        )

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )
        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            birth_time_note=birth_time_note,
            d4_lagna=d4_lagna_str,
            d4_house_lords=d4_house_lords_str,
            d4_planets=d4_planets_str,
            d4_divisions_summary=d4_divisions_summary_str,
            d1_cross_ref=d1_cross_ref_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
        )

    # -------------------------------------------------------------------------
    # Builder: D10 Dashamsha Chart Analysis
    # Placeholders: birth_time_note, d10_lagna, d10_house_lords, d10_planets,
    #   d1_cross_ref, atmakaraka, amatyakaraka, mahadasha, antardasha,
    #   dasha_sequence, user_prompt
    # -------------------------------------------------------------------------
    @classmethod
    def _build_d10_dashamsha_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        def parse_degree(deg_val) -> float:
            if isinstance(deg_val, (int, float)):
                return float(deg_val)
            try:
                if isinstance(deg_val, str) and ":" in deg_val:
                    parts = deg_val.split(":")
                    deg = float(parts[0])
                    min_val = float(parts[1]) if len(parts) > 1 else 0.0
                    sec_val = float(parts[2]) if len(parts) > 2 else 0.0
                    return deg + (min_val / 60.0) + (sec_val / 3600.0)
                return float(deg_val)
            except Exception:
                return 0.0

        birth_time_note = (
            "Birth time provided by user. D10 divisional charts require accurate birth "
            "time — if birth time is approximate or unknown, D10 positions may shift."
        )

        # --- Extract D10 positions ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d10_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D10":
                d10_positions = chart.get("positions", [])
                break

        planet_map = cls._get_d1_planet_map(structured_data)

        # D10 Lagna
        d10_asc = next(
            (p for p in d10_positions if p.get("planet") == "Ascendant"), {}
        )
        d10_lagna_sign = d10_asc.get("sign", "N/A")
        d10_lagna_lord = _sign_lords.get(d10_lagna_sign, "N/A")
        d10_lagna_str = f"{d10_lagna_sign} (Lord: {d10_lagna_lord})"

        # D10 house lords
        d10_planet_map = {p.get("planet"): p for p in d10_positions}
        d10_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d10_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d10_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            try:
                d10_lagna_idx = cls._SIGN_ORDER.index(d10_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d10_house = ((lord_sign_idx - d10_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d10_house = "N/A"
            
            d10_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D10 House {lord_d10_house} ({lord_sign})"
            )
        d10_house_lords_str = "\n".join(d10_house_lord_lines)

        # D10 planetary placements
        d10_planet_lines = []
        for p in d10_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            try:
                d10_lagna_idx = cls._SIGN_ORDER.index(d10_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d10_house_num = ((p_sign_idx - d10_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d10_house_num = "N/A"
            
            p_dignity = p.get("dignity", "N/A")
            p_aspects = p.get("aspects", [])
            
            d10_planet_lines.append(
                f"  {pname} → D10 House: {d10_house_num}"
                f" | Sign: {p_sign}"
                f" | D10 Degree: {p.get('degree', 'N/A')}°"
                f" | Dignity: {p_dignity}"
                f" | Aspects: {p_aspects}"
            )
        d10_planets_str = "\n".join(d10_planet_lines) if d10_planet_lines else "Not available"

        # --- D1 cross-reference ---
        birth_planets = cls._get_birth_planets(structured_data)
        d1_asc = planet_map.get("Ascendant", {})
        d1_lagna_sign = d1_asc.get("sign", "N/A")
        d1_lagna_lord = d1_asc.get("lord", "N/A")
        bp_map = {p.get("planet"): p for p in birth_planets}

        def _d1_lord_of_house(h: int) -> str:
            h_sign = cls._sign_of_house(d1_lagna_sign, h)
            return _sign_lords.get(h_sign, "N/A")

        d1_10th_lord = _d1_lord_of_house(10)

        def _planet_summary(planet_name: str) -> str:
            p = bp_map.get(planet_name, {})
            return (
                f"House {p.get('house', 'N/A')}"
                f" | Sign: {p.get('sign', 'N/A')}"
                f" | Dignity: {p.get('dignity', 'N/A')}"
            )

        d1_cross_ref_str = (
            f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
            f"  D1 10th House Lord: {d1_10th_lord} — {_planet_summary(d1_10th_lord)}\n"
            f"  D1 Sun (Significator of Career/Status) — {_planet_summary('Sun')}\n"
            f"  D1 Saturn (Significator of Work/Service) — {_planet_summary('Saturn')}"
        )

        # Calculate AK and AmK (7-karaka scheme)
        seven_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        planet_degrees_list = []
        for pname in seven_planets:
            p_d1 = planet_map.get(pname, {})
            deg_val = parse_degree(p_d1.get("degree", 0.0))
            planet_degrees_list.append((pname, deg_val))
        
        planet_degrees_list.sort(key=lambda x: x[1], reverse=True)
        ak_planet = planet_degrees_list[0][0] if len(planet_degrees_list) > 0 else "N/A"
        ak_degree = planet_degrees_list[0][1] if len(planet_degrees_list) > 0 else 0.0
        amk_planet = planet_degrees_list[1][0] if len(planet_degrees_list) > 1 else "N/A"
        amk_degree = planet_degrees_list[1][1] if len(planet_degrees_list) > 1 else 0.0
        
        atmakaraka_str = f"{ak_planet} ({ak_degree:.2f}°)"
        amatyakaraka_str = f"{amk_planet} ({amk_degree:.2f}°)"

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )
        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            birth_time_note=birth_time_note,
            d10_lagna=d10_lagna_str,
            d10_house_lords=d10_house_lords_str,
            d10_planets=d10_planets_str,
            d1_cross_ref=d1_cross_ref_str,
            atmakaraka=atmakaraka_str,
            amatyakaraka=amatyakaraka_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
        )

    # -------------------------------------------------------------------------
    # Builder: D7 Saptamsha Chart Analysis
    # Placeholders: birth_time_note, d7_lagna, d7_house_lords, d7_planets,
    #   d1_cross_ref, putrakaraka, mahadasha, antardasha,
    #   dasha_sequence, user_prompt
    # -------------------------------------------------------------------------
    @classmethod
    def _build_d7_saptamsha_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        def parse_degree(deg_val) -> float:
            if isinstance(deg_val, (int, float)):
                return float(deg_val)
            try:
                if isinstance(deg_val, str) and ":" in deg_val:
                    parts = deg_val.split(":")
                    deg = float(parts[0])
                    min_val = float(parts[1]) if len(parts) > 1 else 0.0
                    sec_val = float(parts[2]) if len(parts) > 2 else 0.0
                    return deg + (min_val / 60.0) + (sec_val / 3600.0)
                return float(deg_val)
            except Exception:
                return 0.0

        birth_time_note = (
            "Birth time provided by user. D7 divisional charts require accurate birth "
            "time — if birth time is approximate or unknown, D7 positions may shift."
        )

        # --- Extract D7 positions ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d7_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D7":
                d7_positions = chart.get("positions", [])
                break

        planet_map = cls._get_d1_planet_map(structured_data)

        # D7 Lagna
        d7_asc = next(
            (p for p in d7_positions if p.get("planet") == "Ascendant"), {}
        )
        d7_lagna_sign = d7_asc.get("sign", "N/A")
        d7_lagna_lord = _sign_lords.get(d7_lagna_sign, "N/A")
        d7_lagna_str = f"{d7_lagna_sign} (Lord: {d7_lagna_lord})"

        # D7 house lords
        d7_planet_map = {p.get("planet"): p for p in d7_positions}
        d7_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d7_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d7_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            try:
                d7_lagna_idx = cls._SIGN_ORDER.index(d7_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d7_house = ((lord_sign_idx - d7_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d7_house = "N/A"
            
            d7_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D7 House {lord_d7_house} ({lord_sign})"
            )
        d7_house_lords_str = "\n".join(d7_house_lord_lines)

        # D7 planetary placements
        d7_planet_lines = []
        for p in d7_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            try:
                d7_lagna_idx = cls._SIGN_ORDER.index(d7_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d7_house_num = ((p_sign_idx - d7_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d7_house_num = "N/A"
            
            p_dignity = p.get("dignity", "N/A")
            p_aspects = p.get("aspects", [])
            
            d7_planet_lines.append(
                f"  {pname} → D7 House: {d7_house_num}"
                f" | Sign: {p_sign}"
                f" | D7 Degree: {p.get('degree', 'N/A')}°"
                f" | Dignity: {p_dignity}"
                f" | Aspects: {p_aspects}"
            )
        d7_planets_str = "\n".join(d7_planet_lines) if d7_planet_lines else "Not available"

        # --- D1 cross-reference ---
        birth_planets = cls._get_birth_planets(structured_data)
        d1_asc = planet_map.get("Ascendant", {})
        d1_lagna_sign = d1_asc.get("sign", "N/A")
        d1_lagna_lord = d1_asc.get("lord", "N/A")
        bp_map = {p.get("planet"): p for p in birth_planets}

        def _d1_lord_of_house(h: int) -> str:
            h_sign = cls._sign_of_house(d1_lagna_sign, h)
            return _sign_lords.get(h_sign, "N/A")

        d1_5th_lord = _d1_lord_of_house(5)

        def _planet_summary(planet_name: str) -> str:
            p = bp_map.get(planet_name, {})
            return (
                f"House {p.get('house', 'N/A')}"
                f" | Sign: {p.get('sign', 'N/A')}"
                f" | Dignity: {p.get('dignity', 'N/A')}"
            )

        d1_cross_ref_str = (
            f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
            f"  D1 5th House Lord: {d1_5th_lord} — {_planet_summary(d1_5th_lord)}\n"
            f"  D1 Jupiter (Significator of Progeny) — {_planet_summary('Jupiter')}"
        )

        # Calculate PK (Putrakaraka) - 5th highest degree in 7-karaka scheme (index 4)
        seven_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        planet_degrees_list = []
        for pname in seven_planets:
            p_d1 = planet_map.get(pname, {})
            deg_val = parse_degree(p_d1.get("degree", 0.0))
            planet_degrees_list.append((pname, deg_val))
        
        planet_degrees_list.sort(key=lambda x: x[1], reverse=True)
        pk_planet = planet_degrees_list[4][0] if len(planet_degrees_list) > 4 else "N/A"
        pk_degree = planet_degrees_list[4][1] if len(planet_degrees_list) > 4 else 0.0
        putrakaraka_str = f"{pk_planet} ({pk_degree:.2f}°)"

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )
        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            birth_time_note=birth_time_note,
            d7_lagna=d7_lagna_str,
            d7_house_lords=d7_house_lords_str,
            d7_planets=d7_planets_str,
            d1_cross_ref=d1_cross_ref_str,
            putrakaraka=putrakaraka_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
        )

    # -------------------------------------------------------------------------
    # Builder: D12 Dwadashamsha Chart Analysis
    # Placeholders: birth_time_note, d12_lagna, d12_house_lords, d12_planets,
    #   d1_cross_ref, mahadasha, antardasha, dasha_sequence, user_prompt
    # -------------------------------------------------------------------------
    @classmethod
    def _build_d12_dwadashamsha_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        birth_time_note = (
            "Birth time provided by user. D12 divisional charts require accurate birth "
            "time — if birth time is approximate or unknown, D12 positions may shift."
        )

        # --- Extract D12 positions ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d12_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D12":
                d12_positions = chart.get("positions", [])
                break

        planet_map = cls._get_d1_planet_map(structured_data)

        # D12 Lagna
        d12_asc = next(
            (p for p in d12_positions if p.get("planet") == "Ascendant"), {}
        )
        d12_lagna_sign = d12_asc.get("sign", "N/A")
        d12_lagna_lord = _sign_lords.get(d12_lagna_sign, "N/A")
        d12_lagna_str = f"{d12_lagna_sign} (Lord: {d12_lagna_lord})"

        # D12 house lords
        d12_planet_map = {p.get("planet"): p for p in d12_positions}
        d12_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d12_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d12_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            try:
                d12_lagna_idx = cls._SIGN_ORDER.index(d12_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d12_house = ((lord_sign_idx - d12_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d12_house = "N/A"
            
            d12_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D12 House {lord_d12_house} ({lord_sign})"
            )
        d12_house_lords_str = "\n".join(d12_house_lord_lines)

        # D12 planetary placements
        d12_planet_lines = []
        for p in d12_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            try:
                d12_lagna_idx = cls._SIGN_ORDER.index(d12_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d12_house_num = ((p_sign_idx - d12_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d12_house_num = "N/A"
            
            p_dignity = p.get("dignity", "N/A")
            p_aspects = p.get("aspects", [])
            
            d12_planet_lines.append(
                f"  {pname} → D12 House: {d12_house_num}"
                f" | Sign: {p_sign}"
                f" | D12 Degree: {p.get('degree', 'N/A')}°"
                f" | Dignity: {p_dignity}"
                f" | Aspects: {p_aspects}"
            )
        d12_planets_str = "\n".join(d12_planet_lines) if d12_planet_lines else "Not available"

        # --- D1 cross-reference ---
        birth_planets = cls._get_birth_planets(structured_data)
        d1_asc = planet_map.get("Ascendant", {})
        d1_lagna_sign = d1_asc.get("sign", "N/A")
        d1_lagna_lord = d1_asc.get("lord", "N/A")
        bp_map = {p.get("planet"): p for p in birth_planets}

        def _d1_lord_of_house(h: int) -> str:
            h_sign = cls._sign_of_house(d1_lagna_sign, h)
            return _sign_lords.get(h_sign, "N/A")

        d1_4th_lord = _d1_lord_of_house(4)
        d1_9th_lord = _d1_lord_of_house(9)

        def _planet_summary(planet_name: str) -> str:
            p = bp_map.get(planet_name, {})
            return (
                f"House {p.get('house', 'N/A')}"
                f" | Sign: {p.get('sign', 'N/A')}"
                f" | Dignity: {p.get('dignity', 'N/A')}"
            )

        d1_cross_ref_str = (
            f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
            f"  D1 4th House Lord (Mother): {d1_4th_lord} — {_planet_summary(d1_4th_lord)}\n"
            f"  D1 9th House Lord (Father): {d1_9th_lord} — {_planet_summary(d1_9th_lord)}\n"
            f"  D1 Sun (Father Significator) — {_planet_summary('Sun')}\n"
            f"  D1 Moon (Mother Significator) — {_planet_summary('Moon')}"
        )

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )
        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            birth_time_note=birth_time_note,
            d12_lagna=d12_lagna_str,
            d12_house_lords=d12_house_lords_str,
            d12_planets=d12_planets_str,
            d1_cross_ref=d1_cross_ref_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
        )

    # -------------------------------------------------------------------------
    # Builder: D60 Shashtiamsha Chart Analysis
    # Placeholders: birth_time_note, d60_lagna, d60_house_lords, d60_planets,
    #   d1_cross_ref, mahadasha, antardasha, dasha_sequence, user_prompt
    # -------------------------------------------------------------------------
    @classmethod
    def _build_d60_shashtiamsha_prompt(
        cls, template: str, structured_data: dict, user_prompt: str = ""
    ) -> str:
        _sign_lords = {
            "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
            "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
            "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
        }

        # 60 Shashtiamsha deities and qualities (good vs difficult)
        _deities = {
            1: ("Ghora", "difficult"), 2: ("Rakshasa", "difficult"), 3: ("Deva", "good"), 
            4: ("Kubera", "good"), 5: ("Yaksha", "good"), 6: ("Kinnara", "good"), 
            7: ("Bhrasta", "difficult"), 8: ("Kulaghna", "difficult"), 9: ("Garala", "difficult"), 
            10: ("Agni", "difficult"), 11: ("Maya", "difficult"), 12: ("Purishak", "difficult"), 
            13: ("Apampati", "good"), 14: ("Marut", "good"), 15: ("Kaal", "difficult"), 
            16: ("Sarpa/Ahi", "difficult"), 17: ("Amrit", "good"), 18: ("Indu", "good"), 
            19: ("Mridu", "good"), 20: ("Komala", "good"), 21: ("Heramba", "good"), 
            22: ("Brahma", "good"), 23: ("Vishnu", "good"), 24: ("Mahesh", "good"), 
            25: ("Deva", "good"), 26: ("Ardra", "good"), 27: ("Kalinash", "good"), 
            28: ("Kshitish", "good"), 29: ("Kamlakara", "good"), 30: ("Gulika", "difficult"), 
            31: ("Mrityu", "difficult"), 32: ("Kaal", "difficult"), 33: ("Davagni", "difficult"), 
            34: ("Ghora", "difficult"), 35: ("Yama", "difficult"), 36: ("Kantaka", "difficult"), 
            37: ("Sudha", "good"), 38: ("Amrita", "good"), 39: ("Purnachandra", "good"), 
            40: ("Vishdagdha", "difficult"), 41: ("Kulanash", "difficult"), 42: ("Vanshakshaya", "difficult"), 
            43: ("Utpaat", "difficult"), 44: ("Kaal", "difficult"), 45: ("Soumya", "good"), 
            46: ("Komala", "good"), 47: ("Sheetala", "good"), 48: ("Drinshtakaral", "difficult"), 
            49: ("Indumukh", "good"), 50: ("Praveena", "good"), 51: ("Kalagni", "difficult"), 
            52: ("Dandayudh", "difficult"), 53: ("Nirmala", "good"), 54: ("Soumya", "good"), 
            55: ("Krura", "difficult"), 56: ("Atisheetala", "good"), 57: ("Sudha", "good"), 
            58: ("Payodhi", "good"), 59: ("Bhramana", "difficult"), 60: ("Chandrarekha", "good")
        }

        def is_odd_sign(sign: str) -> bool:
            odd_signs = {"Ari", "Gem", "Leo", "Lib", "Sag", "Aqu"}
            return sign in odd_signs

        def parse_degree(deg_val) -> float:
            if isinstance(deg_val, (int, float)):
                return float(deg_val)
            try:
                if isinstance(deg_val, str) and ":" in deg_val:
                    parts = deg_val.split(":")
                    deg = float(parts[0])
                    min_val = float(parts[1]) if len(parts) > 1 else 0.0
                    sec_val = float(parts[2]) if len(parts) > 2 else 0.0
                    return deg + (min_val / 60.0) + (sec_val / 3600.0)
                return float(deg_val)
            except Exception:
                return 0.0

        def calculate_shashtiamsha(sign: str, deg_str_or_num) -> str:
            d = parse_degree(deg_str_or_num)
            d = d % 30.0
            part = int(d * 2.0) + 1
            if part > 60:
                part = 60
            elif part < 1:
                part = 1
            if not is_odd_sign(sign):
                part = 61 - part
            deity_name, quality = _deities.get(part, ("Unknown", "unknown"))
            return f"{deity_name} ({quality})"

        birth_time_note = (
            "Birth time provided by user. D60 Shashtiamsha divisional chart requires extremely "
            "accurate birth time (to seconds) — if birth time is approximate, unknown, or off by "
            "even a couple of minutes, D60 positions and deities will shift completely."
        )

        # --- Extract D60 positions ---
        divisional_raw = structured_data.get("divisional_data", {})
        all_charts = divisional_raw.get("data", {}).get("charts", [])
        d60_positions = []
        for chart in all_charts:
            if chart.get("chart") == "D60":
                d60_positions = chart.get("positions", [])
                break

        planet_map = cls._get_d1_planet_map(structured_data)

        # D60 Lagna
        d60_asc = next(
            (p for p in d60_positions if p.get("planet") == "Ascendant"), {}
        )
        d60_lagna_sign = d60_asc.get("sign", "N/A")
        d60_lagna_lord = _sign_lords.get(d60_lagna_sign, "N/A")
        
        # Calculate lagna shashtiamsha based on D1 Ascendant
        d1_asc = planet_map.get("Ascendant", {})
        d1_asc_sign = d1_asc.get("sign", "Ari")
        d1_asc_deg = d1_asc.get("degree", 0.0)
        d60_lagna_shashtiamsha = calculate_shashtiamsha(d1_asc_sign, d1_asc_deg)
        d60_lagna_str = f"{d60_lagna_sign} (Lord: {d60_lagna_lord}) | Shashtiamsha: {d60_lagna_shashtiamsha}"

        # D60 house lords
        d60_planet_map = {p.get("planet"): p for p in d60_positions}
        d60_house_lord_lines = []
        for h in range(1, 13):
            h_sign = cls._sign_of_house(d60_lagna_sign, h)
            lord_name = _sign_lords.get(h_sign, "N/A")
            lord_data = d60_planet_map.get(lord_name, {})
            lord_sign = lord_data.get("sign", "N/A")
            try:
                d60_lagna_idx = cls._SIGN_ORDER.index(d60_lagna_sign)
                lord_sign_idx = cls._SIGN_ORDER.index(lord_sign)
                lord_d60_house = ((lord_sign_idx - d60_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                lord_d60_house = "N/A"
            
            d1_lord_data = planet_map.get(lord_name, {})
            d1_lord_sign = d1_lord_data.get("sign", "Ari")
            d1_lord_deg = d1_lord_data.get("degree", 0.0)
            lord_shashtiamsha = calculate_shashtiamsha(d1_lord_sign, d1_lord_deg)
            
            d60_house_lord_lines.append(
                f"  House {h} ({h_sign}) → Lord: {lord_name}"
                f" | In D60 House {lord_d60_house} ({lord_sign})"
                f" | Lord Shashtiamsha: {lord_shashtiamsha}"
            )
        d60_house_lords_str = "\n".join(d60_house_lord_lines)

        # D60 planetary placements
        d60_planet_lines = []
        for p in d60_positions:
            pname = p.get("planet", "")
            if pname == "Ascendant":
                continue
            p_sign = p.get("sign", "N/A")
            try:
                d60_lagna_idx = cls._SIGN_ORDER.index(d60_lagna_sign)
                p_sign_idx = cls._SIGN_ORDER.index(p_sign)
                d60_house_num = ((p_sign_idx - d60_lagna_idx) % 12) + 1
            except (ValueError, AttributeError):
                d60_house_num = "N/A"
            
            p_dignity = p.get("dignity", "N/A")
            p_aspects = p.get("aspects", [])
            
            # calculate shashtiamsha based on D1 position
            d1_p = planet_map.get(pname, {})
            d1_p_sign = d1_p.get("sign", "Ari")
            d1_p_deg = d1_p.get("degree", 0.0)
            p_shashtiamsha = calculate_shashtiamsha(d1_p_sign, d1_p_deg)
            
            d60_planet_lines.append(
                f"  {pname} → D60 House: {d60_house_num}"
                f" | Sign: {p_sign}"
                f" | D60 Degree: {p.get('degree', 'N/A')}°"
                f" | Dignity: {p_dignity}"
                f" | Shashtiamsha: {p_shashtiamsha}"
                f" | Aspects: {p_aspects}"
            )
        d60_planets_str = "\n".join(d60_planet_lines) if d60_planet_lines else "Not available"

        # --- D1 cross-reference ---
        birth_planets = cls._get_birth_planets(structured_data)
        d1_asc = planet_map.get("Ascendant", {})
        d1_lagna_sign = d1_asc.get("sign", "N/A")
        d1_lagna_lord = d1_asc.get("lord", "N/A")
        
        # build flat list of D1 placements for D1 cross-ref
        d1_planet_lines = []
        for bp in birth_planets:
            bp_name = bp.get("planet", "")
            d1_planet_lines.append(
                f"  {bp_name}: House {bp.get('house', 'N/A')} | Sign: {bp.get('sign', 'N/A')} | Dignity: {bp.get('dignity', 'N/A')}"
            )
        d1_planets_str = "\n".join(d1_planet_lines) if d1_planet_lines else "Not available"
        
        d1_cross_ref_str = (
            f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
            f"  D1 Placements:\n{d1_planets_str}"
        )

        # --- Dasha ---
        dasha_raw = structured_data.get("dasha", {})
        current = dasha_raw.get("data", {}).get("current_period", {})
        mahadasha_str = (
            f"{current.get('mahadasha', 'N/A')}"
            f" (ends: {current.get('mahadasha_end', 'N/A')})"
        )
        antardasha_str = (
            f"{current.get('antardasha', 'N/A')}"
            f" (ends: {current.get('antardasha_end', 'N/A')})"
        )
        antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
        dasha_seq_lines = []
        for a in antardashas:
            marker = " (CURRENT)" if a.get("is_current") else ""
            dasha_seq_lines.append(
                f"  {a.get('planet')} Antardasha:"
                f" {a.get('start_date')} → {a.get('end_date')}{marker}"
            )
        dasha_sequence_str = (
            "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
        )

        return template.format(
            user_prompt=user_prompt,
            birth_time_note=birth_time_note,
            d60_lagna=d60_lagna_str,
            d60_house_lords=d60_house_lords_str,
            d60_planets=d60_planets_str,
            d1_cross_ref=d1_cross_ref_str,
            mahadasha=mahadasha_str,
            antardasha=antardasha_str,
            dasha_sequence=dasha_sequence_str,
        )

    @classmethod
    def generate_daily_tara_guidance(
        cls, birth_nakshatra: str, transit_nakshatra: str, tara_type: str
    ) -> dict:
        """
        Generates structured AI guidance for today's Tara Bala.
        Returns a dict matching the requested JSON structure.
        """
        import json
        from google import genai
        from django.conf import settings

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = cls.DAILY_TARA_PROMPT.format(
            birth_nakshatra=birth_nakshatra,
            transit_nakshatra=transit_nakshatra,
            tara_type=tara_type,
        )

        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                },
            )
            return json.loads(response.text)
        except Exception as e:
            from .views import logger

            logger.error(f"Failed to generate daily Tara guidance: {e}")
            return None
