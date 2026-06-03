import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

BENEFIC_PLANETS_PROMPT = """
You are an expert Vedic Astrologer based strictly on Brihat Parasara Hora Sastra principles.

Your task is to identify the benefic planets for a native using functional, natural, and situational logic.

-----------------------------------
INPUT DATA:

Ascendant (Lagna):
{lagna}

Planetary Placements:
{planets}

D9 (Navamsa) Chart:
{d9_data}

Dasha (optional):
{dasha}
-----------------------------------

ANALYSIS FRAMEWORK:

1. FUNCTIONAL BENEFICS (BY LAGNA)
- Identify benefic planets based on Ascendant-specific rules
- Determine Yogakaraka planets:
  - Planets owning both Kendra (1,4,7,10) and Trikona (1,5,9)

2. NATURAL BENEFICS
- Jupiter, Venus, Mercury, Waxing Moon

3. STRENGTH & DIGNITY
- Check: Exalted (Ucha), Own sign (Swakshetra), Friendly sign
- Strong natural malefics (e.g., Saturn/Mars in own/exaltation/Kendra/Trikona) can behave as benefics

4. SITUATIONAL MODIFIERS
- House Placement: Planets in 2, 5, 8, 9 -> wealth and happiness
- Benefic Aspects / Argala: Check if supported by benefics or own lord
- Weakening Factors: Benefics in 6, 8, 12 may give malefic results

5. D9 VALIDATION (MANDATORY)
- Cross-check strength in Navamsa (D9)
- Identify Vargottama planets

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Functional Benefics:
- Based on Lagna

Natural Benefics:
- List

Strong Benefics:
- Based on dignity + placement

Conditional Benefics:
- Malefics behaving as benefics (with reasoning)

Final Benefic Planets:
- Consolidated list

Reasoning:
- Clear explanation for each planet
"""

def build_benefic_planets_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")

    birth_planets = get_birth_planets(structured_data)
    planet_lines = []
    for p in birth_planets:
        planet_lines.append(
            f"  {p.get('planet')} - {p.get('sign')} - House {p.get('house')}"
        )
    planets_str = "\n".join(planet_lines) if planet_lines else "Not available"

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
