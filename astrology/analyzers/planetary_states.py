import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

PLANETARY_STATES_PROMPT = """
You are an expert Vedic Astrologer specializing in planetary states (Avasthas) and Dasha quality.

Your task is to determine each planet’s condition and its ability to deliver results.

-----------------------------------
INPUT DATA:
{astrology_data}

D9 (Navamsa) Placement:
{d9_data}
-----------------------------------

ANALYSIS FRAMEWORK:

1. AVASTHA (STATE)
Classify:
- Deepta -> exalted
- Swastha -> own sign
- Mudita -> friend sign
- Shanta -> benefic environment
- Shakta -> retro/combust but active
- Peedita -> combust/afflicted
- Deena -> debilitated
- Vikala -> multi-malefic afflicted
- Khala -> defeated in war

2. AGE STATE (DEGREE BASED)
- Baala (infant)
- Kumara (youth)
- Vridha (old)
- Mrita (dead)

3. DASHA QUALITY
Classify:
- Arohini -> moving toward exaltation
- Avrohini -> moving toward debilitation
- Poorna -> full strength
- Rikta -> empty/weak
- Arishta -> misfortune
- Mishrita -> mixed
- Shubha -> auspicious
- Adhama -> highly malefic

4. D9 VALIDATION
- Check Vargottama
- Confirm strength vs D1

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Planetary State:
- Avastha classification

Age State:
- Degree-based category

Dasha Quality:
- Strength classification

Strength Score:
- Strong / Moderate / Weak

Final Interpretation:
- Ability to deliver results

Notes:
- Any special conditions (combustion, retrograde, etc.)
"""

def build_planetary_states_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
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

    return template.format(
        user_prompt=user_prompt,
        astrology_data=d1_str,
        d9_data=d9_str,
    )
