import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

DARAKARAKA_PROMPT = """
You are an expert Vedic Astrologer specializing in Jaimini Astrology.

Your task is to analyze the Darakaraka (DK) to understand spouse characteristics, relationship dynamics, and karmic responsibilities.

-----------------------------------
INPUT DATA:

Planetary Degrees (D1):
{planet_degrees}

D9 (Navamsa) Chart:
{d9_data}

Current Transits:
{transits}
-----------------------------------

ANALYSIS FRAMEWORK:

1. IDENTIFY DARAKARAKA
- Select the planet with the lowest degree (excluding Rahu/Ketu)
- This planet becomes Darakaraka (DK)

2. CORE INTERPRETATION
- DK represents: Spouse, Relationship dynamics, Karmic responsibility in partnerships

3. PLANET-WISE DK MEANINGS
- Sun -> dominant, leadership traits, ego-driven tendencies
- Moon -> emotional, nurturing, sensitive partner
- Mars -> energetic, active, possibly aggressive
- Mercury -> communicative, youthful, business-minded
- Jupiter -> wise, supportive, growth-oriented
- Venus -> romantic, attractive, artistic
- Saturn -> loyal, stable, serious, long-term commitment

Incorporate the Planetary Avatars for rich contextual flavor:
(Sun=Rama, Moon=Krishna, Mars=Narasimha, Mercury=Buddha, Jupiter=Vamana, Venus=Parashurama, Saturn=Koorma)

4. VALIDATION (MANDATORY)
- Analyze D9 chart placement of DK
- Check dignity (strong/weak/afflicted)

5. SYNTHESIS
- Describe: Spouse personality, Relationship dynamics, Strengths and risks, Karmic lesson

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Darakaraka Planet:
- Identified DK + degree

Spouse Characteristics:
- Based on DK planet

Relationship Dynamics:
- Power balance, emotional tone

D9 Validation:
- Strength and placement impact

Risks & Challenges:
- Potential issues in relationship

Final Insight:
- Karmic lesson and relationship guidance
"""

def build_darakaraka_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)

    degree_lines = []
    for name, data in planet_map.items():
        if name not in ("Ascendant", "Rahu", "Ketu"):
            degree_lines.append(
                f"  {name}: {data.get('degree', 'N/A')}° in {data.get('sign', 'N/A')}"
            )
    planet_degrees = "\n".join(degree_lines) if degree_lines else "Not available"

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
