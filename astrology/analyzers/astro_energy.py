import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

ASTRO_ENERGY_PROMPT = """
You are an expert Vedic Astrologer specializing in energy-based house interpretation.

Your task is to analyze the 12 houses as energy dimensions of life.

-----------------------------------
INPUT DATA:
Lagna: {lagna}
Planetary Placements: {planets}
-----------------------------------

ANALYSIS FRAMEWORK:

Each house represents a dimension of energy:

1st -> Self / Identity  
2nd -> Wealth / Speech  
3rd -> Effort / Courage  
4th -> Emotional Security  
5th -> Creativity / Intelligence  
6th -> Conflict / Health  
7th -> Relationships  
8th -> Transformation  
9th -> Luck / Dharma  
10th -> Career  
11th -> Gains  
12th -> Loss / Liberation  

-----------------------------------

TASK:

For each house:

1. Identify:
- Planets present
- House lord strength

2. Evaluate energy:
- Strong -> empowered dimension
- Weak -> blocked or challenged

3. Translate into real-life behavior:
- Action-oriented interpretation

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

House-wise Energy Analysis:

House 1:
- Energy level + meaning

House 2:
- Energy level + meaning

... continue till House 12 ...

Energy Summary:
- Top 3 strongest dimensions
- Top 3 weakest dimensions

Action Guidance:
- Where to focus effort
- Where to avoid risk

Final Insight:
- Overall life energy distribution
"""

def build_astro_energy_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")

    birth_planets = get_birth_planets(structured_data)
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
