import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

CHART_ANALYSIS_PROMPT = """
You are a Master Vedic Astrologer specializing in Parasari and Jaimini systems.

Your task is to provide an integrated life analysis using D1 (Rashi) and D9 (Navamsa).

-----------------------------------
INPUT DATA:
Lagna: {lagna}
D1 Chart: {d1_data}
D9 Chart: {d9_data}
Current Dasha: {dasha}
-----------------------------------

ANALYSIS FRAMEWORK:

1. CORE IDENTITY (LAGNA)
- Analyze Lagna Lord in D1
- Cross-check in D9:
  - Vargottama / Exalted / Debilitated

2. PLANETARY RESULTS (D1 vs D9)
- Vargottama -> strong
- Exalted D1 but weak D9 -> deceptive strength
- Weak D1 but strong D9 -> hidden potential

3. CAREER ANALYSIS
- Analyze 10th Lord (D1 + D9)
- Analyze Amatyakaraka (career indicator)

4. YOGAS
- Identify:
  - Raja Yoga
  - Dhana Yoga
- Validate if supported in D9

5. DASHA ANALYSIS
- Evaluate current Mahadasha
- Check dignity in D9

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Executive Summary:
- 2-3 line life overview

Key Strengths:
- Top 3 strong factors

Hidden Strengths:
- Late success / Neecha Bhanga indicators

Critical Warnings:
- Weak areas or risks

Career Direction:
- Based on 10th lord + Amatyakaraka

Dasha Guidance:
- Current timing insights
"""

def build_chart_analysis_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")

    birth_planets = get_birth_planets(structured_data)
    d1_str = (
        json.dumps(birth_planets, indent=2) if birth_planets else "Not available"
    )

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
