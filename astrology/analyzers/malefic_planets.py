import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

MALEFIC_PLANETS_PROMPT = """
You are an expert Vedic Astrologer following Brihat Parasara Hora Sastra.

Your task is to identify malefic planets using natural, functional, and situational rules.

-----------------------------------
INPUT DATA:
Ascendant (Lagna): {lagna}
Planetary Placements: {planets}
D9 (Navamsa) Chart: {d9_data}
Dasha (optional): {dasha}
-----------------------------------

ANALYSIS FRAMEWORK:

1. NATURAL MALEFICS
- Sun, Mars, Saturn, Rahu, Ketu, Waning Moon

2. FUNCTIONAL MALEFICS (BY LAGNA)
- Lords of:
  - 6th, 8th, 12th (Trik houses)
  - 2nd, 7th (Maraka)
  - 3rd, 6th, 11th (Upachaya influence)

3. WEAKENED PLANETS
- Debilitated (Neecha)
- Combust (Astangata)
- In inimical sign

4. TRIK HOUSE PLACEMENT
- Any planet in 6, 8, 12 -> can act malefic

5. MALEFIC COMBINATIONS
- Papa Kartari Yoga (planet/lagna/moon hemmed by malefics)
- Mars + Saturn -> harsh effects
- Rahu/Ketu in 8 or 12 -> instability

6. MOON CONDITION
- Weak/waning/debilitated -> mental instability

7. D9 VALIDATION
- Confirm strength or weakness via Navamsa

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Natural Malefics:
- List

Functional Malefics:
- Based on Lagna

Conditionally Malefic:
- Due to placement or weakness

Critical Combinations:
- Harmful yogas or placements

Final Malefic Planets:
- Consolidated list

Risk Summary:
- Key areas of concern
"""

def build_malefic_planets_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
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
