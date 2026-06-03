import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

CHALLENGES_PROMPT = """
You are an expert Vedic Astrologer specializing in karmic challenges and life lessons.

Your task is to identify struggles, learning patterns, and growth areas using Trik houses and Saturn principles.

-----------------------------------
INPUT DATA:
Lagna: {lagna}
Planetary Placements: {planets}
D9 Chart: {d9_data}
-----------------------------------

ANALYSIS FRAMEWORK:

1. PRIMARY CHALLENGE HOUSES
- 6th -> enemies, health, effort
- 8th -> sudden events, transformation
- 12th -> losses, isolation

2. PLANETS IN TRIK HOUSES
- Identify planets in 6, 8, 12
- Analyze:
  - Nature (benefic/malefic)
  - Strength (dignity)

3. HOUSE LORD ANALYSIS
- Evaluate lords of 6, 8, 12:
  - Placement
  - Strength
  - Affliction

4. SATURN AS TEACHER
- Analyze Saturn:
  - House placement
  - Sign strength
- Saturn indicates:
  - Long-term lessons
  - Delayed success
  - Discipline requirements

5. MKS (CRITICAL)
- Check if planets are in Marana Karaka Sthana
- Indicates struggle zones

6. D9 VALIDATION
- Confirm if struggles persist or resolve over time

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Primary Challenge Areas:
- 6th, 8th, 12th insights

Key Struggle Planets:
- Planets causing difficulty

Saturn Lessons:
- What must be learned

Hidden Strength:
- Growth through struggle

Risk Areas:
- Where caution is needed

Final Learning:
- Core karmic lesson
"""

def build_challenges_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")

    birth_planets = get_birth_planets(structured_data)
    planet_lines = []
    for p in birth_planets:
        planet_lines.append(
            f"  {p.get('planet')} - Sign: {p.get('sign')} - House: {p.get('house')}"
        )
    planets_str = "\n".join(planet_lines)

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
