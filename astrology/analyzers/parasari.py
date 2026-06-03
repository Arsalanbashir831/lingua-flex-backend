import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

PARASARI_PROMPT = """
You are an expert Vedic Astrologer specializing in Brihat Parasara Hora Sastra principles.

Your task is to analyze planetary relationships using:
- Moolatrikona
- Natural Relationships (Naisargika Maitri)
- Temporary Relationships (Tatkalika Maitri)
- Compound Relationships (Panchadha Maitri)

-----------------------------------
INPUT DATA (D1 Chart):
Ascendant (Lagna): {lagna}

Planets:
Sun: {sun}
Moon: {moon}
Mars: {mars}
Mercury: {mercury}
Jupiter: {jupiter}
Venus: {venus}
Saturn: {saturn}
Rahu: {rahu}
Ketu: {ketu}
-----------------------------------

RULES:

1. MOOLATRIKONA DEFINITIONS
- Sun -> Leo (0-20)
- Moon -> Taurus (4-30)
- Mars -> Aries (0-12)
- Mercury -> Virgo (16-20)
- Jupiter -> Sagittarius (0-10)
- Venus -> Libra (0-15)
- Saturn -> Aquarius (0-20)

2. NATURAL RELATIONSHIPS
- Friends -> Lords of 2nd, 4th, 5th, 8th, 9th, 12th from Moolatrikona + exaltation lord
- Enemies -> Lords of 3rd, 6th, 7th, 10th, 11th
- Others -> Neutral

3. TEMPORARY RELATIONSHIPS (D1 placement)
- Friends -> planets in 2,3,4,10,11,12 from a planet
- Enemies -> all other positions

4. COMPOUND RELATIONSHIPS (PANCHADHA MAITRI)
Combine natural + temporary:
- Friend + Friend -> Great Friend (Adhi Mitra)
- Friend + Neutral -> Friend (Mitra)
- Enemy + Neutral -> Enemy (Shatru)
- Enemy + Enemy -> Great Enemy (Adhi Shatru)
- Friend + Enemy -> Neutral (Sama)

-----------------------------------

TASK:
1. Identify Moolatrikona sign for each planet
2. Calculate Natural Relationships for each planet
3. Determine Temporary Relationships using D1 positions
4. Combine into Compound Relationships (Panchadha Maitri)
5. Identify strongest supportive planets (Great Friends)

{user_prompt}
-----------------------------------

OUTPUT FORMAT:

Moolatrikona Mapping:
- Each planet -> its Moolatrikona

Natural Relationships:
- Planet-wise friends / enemies / neutral

Temporary Relationships:
- Based on placements

Compound Relationships:
- Final classification (Adhi Mitra / Mitra / Sama / Shatru / Adhi Shatru)

Key Support Planets:
- List most beneficial planets for the native

Summary:
- Overall planetary harmony/conflict
"""

def build_parasari_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    planet_map = get_d1_planet_map(structured_data)
    birth_planets = get_birth_planets(structured_data)
    house_map = {p.get("planet"): p.get("house", "N/A") for p in birth_planets}

    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")

    def planet_str(name):
        p = planet_map.get(name, {})
        return (
            f"Sign: {p.get('sign', 'N/A')}, "
            f"House: {house_map.get(name, 'N/A')}, "
            f"Degree: {p.get('degree', 'N/A')}, "
            f"Lord of sign: {p.get('lord', 'N/A')}"
        )

    return template.format(
        user_prompt=user_prompt,
        lagna=f"{lagna_sign} (Lord: {lagna_lord})",
        sun=planet_str("Sun"),
        moon=planet_str("Moon"),
        mars=planet_str("Mars"),
        mercury=planet_str("Mercury"),
        jupiter=planet_str("Jupiter"),
        venus=planet_str("Venus"),
        saturn=planet_str("Saturn"),
        rahu=planet_str("Rahu"),
        ketu=planet_str("Ketu"),
    )
