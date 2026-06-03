import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

MASTER_SAV_PROMPT = """
You are an expert Vedic Astrologer specializing in advanced Sarvashtak Varga (SAV) analysis.

Your task is to analyze SAV data using combined methodologies:
- Gurudev Sunil Vashist
- Astro Intelligence
- Nakshatra Tak enhancements

-----------------------------------
INPUT DATA:
Lagna (Ascendant): {lagna}

SAV Points by House:
{sav_house_points}

Current Saturn Transit House: {saturn_house}
-----------------------------------

ANALYSIS FRAMEWORK:

1. HOUSE MAPPING
- Map Lagna to House 1
- Assign remaining houses sequentially

2. LIFE PROSPERITY FORMULA (164 RULE)
- Sum Houses: 1 + 2 + 4 + 9 + 10 + 11

Interpretation:
- >=164 -> strong prosperity and comfort
- <164 -> increasing struggle depending on deficit

3. STRENGTH + STRUGGLE RULES
- Average: 28
- Weak: <27
- Dented: <22

Struggle Rule:
- If any two of Houses 6, 8, 12 > House 1 -> high struggle life

4. MARAKA EXCEPTION
- Houses 2 and 7 ideal range: 22-28
- >28 -> complications

5. LUCKY DIRECTION ANALYSIS

Calculate total SAV points:
- East -> Houses (1,5,9)
- South -> Houses (2,6,10)
- West -> Houses (3,7,11)
- North -> Houses (4,8,12)

- Identify highest scoring direction
- Recommend for business, growth, residence

6. CAREER & WEALTH DYNAMICS

- Business Rule:
  Recommend business only if H11 >= H10
  Else -> job recommended

- Wealth Flow:
  If H2 > H12 -> savings
  Else -> losses

- Relationship Influence:
  Compare H1 vs H7
  Higher value -> dominant partner/self

7. SADE SATI IMPACT
- Evaluate Saturn transit house score:
  If SAV >28 -> Sade Sati favorable
  If SAV <28 -> challenging period

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Prosperity Score:
- Total (out of 164 rule)
- Interpretation

House Strength Summary:
- Weak and dented houses

Struggle Analysis:
- Whether struggle rule is triggered

Lucky Direction:
- Best direction (East/South/West/North)
- Recommendation

Career Recommendation:
- Job vs Business (with logic)

Wealth Analysis:
- Savings vs losses

Relationship Dynamics:
- Dominant side (self vs partner)

Sade Sati Impact:
- Favorable or difficult

Final Summary:
- Clear, practical life guidance
"""

def build_sav_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    lagna_sign = planet_map.get("Ascendant", {}).get("sign", "N/A")
    lagna_lord = planet_map.get("Ascendant", {}).get("lord", "N/A")

    sav_raw = structured_data.get("ashtakvarga", {})
    house_breakdown = (
        sav_raw.get("data", {})
        .get("sarvashtakvarga", {})
        .get("house_breakdown", [])
    )
    sav_lines = []
    for h in house_breakdown:
        sav_lines.append(
            f"  House {h.get('house')} ({h.get('sign')}): "
            f"{h.get('total_bindus')} bindus [{h.get('strength')}] - {h.get('house_theme')}"
        )
    sav_house_points = "\n".join(sav_lines) if sav_lines else "Not available"

    birth_planets = get_birth_planets(structured_data)
    saturn_house = next(
        (
            p.get("house", "N/A")
            for p in birth_planets
            if p.get("planet") == "Saturn"
        ),
        "N/A",
    )

    return template.format(
        user_prompt=user_prompt,
        lagna=f"{lagna_sign} (Lord: {lagna_lord})",
        sav_house_points=sav_house_points,
        saturn_house=saturn_house,
    )
