"""
AstrologyAPIClient — thin wrapper around api.astrology-api.io v3 Vedic endpoints.

All methods return the parsed JSON response dict directly.
Raises AstrologyAPIError on any failure (non-2xx status, network error, etc.).
"""

import requests
from django.conf import settings
from .analyzers import (
    build_mental_health_prompt,
    build_btr_prompt,
    build_marriage_prompt,
    build_d2_hora_prompt,
    build_d4_chaturthamsha_prompt,
    build_d10_dashamsha_prompt,
    build_d7_saptamsha_prompt,
    build_d12_dwadashamsha_prompt,
    build_d60_shashtiamsha_prompt,
    build_d27_saptavimshamsha_prompt,
    build_benefic_planets_prompt,
    build_malefic_planets_prompt,
    build_chart_analysis_prompt,
    build_planetary_states_prompt,
    build_lagna_lord_prompt,
    build_rashi_planets_prompt,
    build_challenges_prompt,
    build_astro_energy_prompt,
    build_sav_prompt,
    build_parasari_prompt,
    build_navatara_prompt,
    build_medical_prompt,
    build_darakaraka_prompt,
    build_foreign_travel_prompt,
)

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

    def get_festival_calendar(
        self, year: int, festival_type: str = None, language: str = None, region: str = None
    ) -> dict:
        """
        Calls POST /vedic/festival-calendar.
        Returns the festival calendar for the given year and optional filters.
        """
        payload = {
            "year": year,
        }
        if festival_type:
            payload["festival_type"] = festival_type
        if language:
            payload["language"] = language
        if region:
            payload["region"] = region
        return self._post("festival-calendar", payload)


class GeminiAIError(Exception):
    """Raised when GenAI generation fails."""

    pass


class GeminiAIService:
    from .analyzers import (
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
        D27_SAPTAVIMSHAMSHA_PROMPT,
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
        "d27_saptavimshamsha": D27_SAPTAVIMSHAMSHA_PROMPT,
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
            prompt = build_mental_health_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "btr":
            prompt = build_btr_prompt(
                prompt_template,
                structured_data,
                extra_context or {},
                user_prompt=user_prompt_text,
            )
        elif category == "marriage":
            prompt = build_marriage_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "prosperity_sav":
            prompt = build_sav_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "parasari":
            prompt = build_parasari_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "navatara":
            prompt = build_navatara_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "medical":
            prompt = build_medical_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "darakaraka":
            prompt = build_darakaraka_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "benefic_planets":
            prompt = build_benefic_planets_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "malefic_planets":
            prompt = build_malefic_planets_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "chart_analysis":
            prompt = build_chart_analysis_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "planetary_states":
            prompt = build_planetary_states_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "lagna_lord":
            prompt = build_lagna_lord_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "rashi_planets":
            prompt = build_rashi_planets_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "challenges":
            prompt = build_challenges_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "astro_energy":
            prompt = build_astro_energy_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "foreign_travel":
            prompt = build_foreign_travel_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d2_hora":
            prompt = build_d2_hora_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d4_chaturthamsha":
            prompt = build_d4_chaturthamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d10_dashamsha":
            prompt = build_d10_dashamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d7_saptamsha":
            prompt = build_d7_saptamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d12_dwadashamsha":
            prompt = build_d12_dwadashamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d60_shashtiamsha":
            prompt = build_d60_shashtiamsha_prompt(
                prompt_template, structured_data, user_prompt=user_prompt_text
            )
        elif category == "d27_saptavimshamsha":
            prompt = build_d27_saptavimshamsha_prompt(
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
