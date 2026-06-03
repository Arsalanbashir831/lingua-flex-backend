import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

LAGNA_LORD_PROMPT = """
You are an expert Vedic Astrologer specializing in Lagna-based life direction analysis.

Your task is to analyze the Lagna Lord as the primary “driver of destiny” and determine life path, strengths, and direction.

-----------------------------------
INPUT DATA:
Lagna (Ascendant): {lagna}
Lagna Lord: {lagna_lord}

D1 Placement:
- Sign: {d1_sign}
- House: {d1_house}

D9 Placement:
- Sign: {d9_sign}
- House: {d9_house}

Condition:
- Degrees: {degrees}
- Combust/Retrograde: {condition}
-----------------------------------

ANALYSIS FRAMEWORK:

1. CORE IDENTITY DRIVER
- Lagna Lord defines:
  - Personality
  - Life direction
  - Decision-making ability

2. HOUSE PLACEMENT ANALYSIS
- Interpret life focus based on house:
  1 -> self-driven
  2 -> wealth/speech
  3 -> effort/skills
  4 -> emotional/home
  5 -> creativity/intelligence
  6 -> struggle/service
  7 -> relationships/business
  8 -> transformation/uncertainty
  9 -> luck/dharma
  10 -> career/public image
  11 -> gains/network
  12 -> losses/spirituality

3. SIGN STRENGTH
- Exalted / Own / Friendly -> strong
- Debilitated / enemy -> weak

4. D9 VALIDATION (MANDATORY)
- Check:
  - Vargottama
  - Strength improvement or decline

5. SPECIAL CONDITIONS
- MKS (Marana Karaka Sthana)
- Combustion
- Retrograde influence

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Lagna Lord Overview:
- Planet + placement summary

Life Direction:
- Primary focus area

Strength Analysis:
- Strong / Moderate / Weak

D9 Validation:
- Real strength vs surface strength

Key Opportunities:
- Where growth comes easily

Challenges:
- Where effort is required

Final Insight:
- Clear life path guidance
"""

def build_lagna_lord_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord_name = asc.get("lord", "N/A")

    birth_planets = get_birth_planets(structured_data)
    ll_d1 = next(
        (p for p in birth_planets if p.get("planet") == lagna_lord_name), {}
    )

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
