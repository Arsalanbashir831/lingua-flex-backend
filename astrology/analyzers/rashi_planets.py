import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house

RASHI_PLANETS_PROMPT = """
You are an expert Vedic Astrologer specializing in house lord (Rashi lord) interpretation.

Your task is to analyze how each house lord (“manager of destiny”) operates in the chart.

-----------------------------------
INPUT DATA:
Lagna: {lagna}

House Lords:
1st Lord: {h1}
2nd Lord: {h2}
3rd Lord: {h3}
4th Lord: {h4}
5th Lord: {h5}
6th Lord: {h6}
7th Lord: {h7}
8th Lord: {h8}
9th Lord: {h9}
10th Lord: {h10}
11th Lord: {h11}
12th Lord: {h12}

Planetary Placements:
{placements}
-----------------------------------

ANALYSIS FRAMEWORK:

1. HOUSE LORD LOGIC
- Each lord carries results of its house to the house it sits in

2. INTERPRETATION RULE
For each house lord:
- Identify:
  - House it owns
  - House it is placed in

- Meaning:
  “House X matters manifest in House Y”

Example:
- 2nd lord in 10th -> wealth through career
- 5th lord in 11th -> gains from creativity

3. STRENGTH CHECK
- Dignity:
  - Exalted / own -> strong results
  - Debilitated -> weak

4. CONNECTION ANALYSIS
- Link between:
  - 1, 5, 9 -> Dharma
  - 2, 6, 10 -> Artha
  - 3, 7, 11 -> Kama
  - 4, 8, 12 -> Moksha

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

House Lord Mapping:
- Each lord with placement

Key Life Patterns:
- Major house-to-house connections

Wealth Indicators:
- Based on 2nd, 11th, 10th

Career Flow:
- Based on 10th lord placement

Relationship Indicators:
- Based on 7th lord

Strength Summary:
- Strong vs weak lords

Final Insight:
- How life areas interact
"""


def build_rashi_planets_prompt(
    template: str, structured_data: dict, user_prompt: str = ""
) -> str:
    planet_map = get_d1_planet_map(structured_data)
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

    house_lords = {}
    for h in range(1, 13):
        h_sign = sign_of_house(lagna_sign, h - 1)
        lord_name = sign_lords.get(h_sign, "N/A")
        birth_planets = get_birth_planets(structured_data)
        p_data = next((p for p in birth_planets if p.get("planet") == lord_name), {})
        lord_house = p_data.get("house", "N/A")
        lord_sign = p_data.get("sign", "N/A")

        house_lords[f"h{h}"] = f"{lord_name} in House {lord_house} ({lord_sign})"

    placements_data = get_birth_planets(structured_data)
    placements_str = json.dumps(placements_data, indent=2)

    return template.format(
        user_prompt=user_prompt,
        lagna=f"{lagna_sign} (Lord: {lagna_lord})",
        placements=placements_str,
        **house_lords,
    )
