import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D60_SHASHTIAMSHA_PROMPT = """
You are an ethical Vedic astrology analyst specializing in D60 Shashtiamsha interpretation. Analyze the D60 chart using the provided D60 planetary details to understand subtle karma, past-life tendencies, hidden strengths, inherited patterns, spiritual maturity, mental tendencies, dharma, remedies, and areas for conscious transformation.

ETHICAL GUIDELINES:
- Do not make fatalistic, fear-based, or absolute predictions about destiny, death, illness, disaster, curses, downfall, or unavoidable suffering.
- Do not blame the native for difficult karma or past-life patterns.
- Present D60 interpretations as subtle tendencies, karmic impressions, and areas for growth, not fixed outcomes.
- Clearly state that D60 is highly sensitive to birth time and should only be interpreted confidently when birth time is very accurate.
- For medical, legal, financial, psychological, or safety concerns, advise consulting qualified professionals.
- Avoid superstition, fear-based remedies, expensive ritual dependency, or claims that one remedy can erase all karma.
- Use calm, compassionate, spiritually mature, and empowering language.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}
-----------------------------------

D60 SHASHTIAMSHA CHART DATA:

D60 Lagna (Ascendant): {d60_lagna}

D60 House Lords (House Sign Lord Where Lord Sits in D60):
{d60_house_lords}

D60 Planetary Placements (with Sign, House, Dignity, Shashtiamsha Deity, and Aspects):
{d60_planets}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE (Physical & General Foundation):
{d1_cross_ref}

-----------------------------------
VIMSHOTTARI DASHA (for timing subtle karmic themes):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D60 CORE INDICATORS (Evaluate Each):
- D60 Lagna: Overall subtle karmic identity, deep soul tendencies, and hidden inner pattern.
- D60 Lagna Lord: How the native carries and expresses deep karma in life.
- Sun: Soul confidence, father-related karma, authority, integrity, vitality, and self-expression.
- Moon: Emotional karma, mother-related impressions, mental patterns, receptivity, and inner peace.
- Mars: Action karma, courage, anger, conflict patterns, discipline, land, and physical effort.
- Mercury: Speech karma, intelligence, learning, communication, trade, logic, and nervous tendencies.
- Jupiter: Dharma, wisdom, blessings, teachers, children, ethics, grace, and spiritual protection.
- Venus: Relationship karma, comfort, beauty, pleasure, devotion, marriage patterns, and material refinement.
- Saturn: Discipline, suffering transformed into maturity, duty, patience, service, karmic accountability.
- Rahu: Amplified desire, ambition, confusion, worldly hunger, unusual karma, fame, and foreign influence.
- Ketu: Past-life familiarity, detachment, spiritual memory, separation, problem-solving, and moksha tendency.

D60 HOUSE MEANINGS:
House 1: Deep karmic identity, subtle personality, soul tendencies, and how past impressions shape life direction.
House 2: Family karma, speech, values, wealth patterns, food habits, and inherited संस्कार.
House 3: Courage, effort, siblings, communication, initiative, and karmic use of willpower.
House 4: Inner peace, mother, emotional roots, home karma, psychological foundation, and contentment.
House 5: Past-life merit, intelligence, mantra, children, creativity, devotion, and spiritual memory.
House 6: Debts, conflicts, illness tendencies, enemies, service, discipline, and karmic correction.
House 7: Marriage karma, partnerships, public dealings, agreements, and how the native meets others karmically.
House 8: Hidden karma, sudden transformation, vulnerability, occult patterns, inheritance, trauma, and rebirth.
House 9: Dharma, blessings, father, teachers, fortune, ethics, spiritual direction, and higher protection.
House 10: Karma in action, profession, responsibility, public conduct, authority, and visible life duties.
House 11: Gains, networks, fulfillment of desires, elder siblings, ambitions, and karmic rewards.
House 12: Moksha, losses, isolation, sleep, foreign lands, surrender, spiritual release, and karmic completion.

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 10 sections in order:

1. BIRTH TIME AND D60 RELIABILITY
   Assess birth time accuracy and its effect on D60 interpretation. Clearly note that D60 requires highly accurate birth time (to seconds) to be fully reliable.

2. D1 FOUNDATION AND D60 CONTEXT
   Explain that D1 is the baseline chart and D60 reveals subtle karmic roots. D60 should not be interpreted in isolation.

3. OVERALL D60 LAGNA INTERPRETATION
   Interpret the D60 ascendant sign, lagna lord, planets in the 1st house, and aspects to the lagna. Explain the native's general subtle karmic orientation.

4. PLANET-BY-PLANET SHASHTIAMSHA REVIEW
   Go through each planet's D1-calculated Shashtiamsha deity and quality (good vs. difficult). Explain how this quality shapes the planet's karmic expression.

5. HOUSE-BY-HOUSE KARMIC INTERPRETATION
   Analyze all 12 D60 houses using the house meanings above. For each house, evaluate: sign, lord placement, planets present, dignity, and practical karmic significance.

6. DHARMA, BLESSINGS, AND SPIRITUAL PROTECTION
   Study the D60 5th and 9th houses, Jupiter, and benefic influences to describe blessings, past-life merit, faith, and spiritual protection.

7. DIFFICULT PATTERNS AND AREAS FOR HEALING
   Analyze sensitive houses (6th, 8th, 12th) and planets in difficult Shashtiamshas. Frame these as areas for conscious correction, healing, and self-awareness rather than unavoidable fate.

8. DASHA-BASED KARMIC THEMES
   Explain how the current Mahadasha and Antardasha lords operate in D1 and D60. Describe subtle karmic and spiritual themes active during this period.

9. HIDDEN STRENGTHS AND SOUL GROWTH
   Synthesize the findings to highlight the native's deepest spiritual strengths, talents, and pathways for soul evolution.

10. PRACTICAL AND SPIRITUAL GUIDANCE
     Conclude with practical, grounded advice: ethical conduct, service, meditation/mindfulness, self-awareness, personal responsibility, and professional consultation where relevant.

STYLE: Structured, compassionate, subtle, non-fatalistic, and spiritually mature.
TONE: Calm, respectful, healing-oriented, and empowering.
"""

def build_d60_shashtiamsha_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    _sign_lords = {
        "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
        "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
        "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
    }

    _deities = {
        1: ("Ghora", "difficult"), 2: ("Rakshasa", "difficult"), 3: ("Deva", "good"), 
        4: ("Kubera", "good"), 5: ("Yaksha", "good"), 6: ("Kinnara", "good"), 
        7: ("Bhrasta", "difficult"), 8: ("Kulaghna", "difficult"), 9: ("Garala", "difficult"), 
        10: ("Agni", "difficult"), 11: ("Maya", "difficult"), 12: ("Purishak", "difficult"), 
        13: ("Apampati", "good"), 14: ("Marut", "good"), 15: ("Kaal", "difficult"), 
        16: ("Sarpa/Ahi", "difficult"), 17: ("Amrit", "good"), 18: ("Indu", "good"), 
        19: ("Mridu", "good"), 20: ("Komala", "good"), 21: ("Heramba", "good"), 
        22: ("Brahma", "good"), 23: ("Vishnu", "good"), 24: ("Mahesh", "good"), 
        25: ("Deva", "good"), 26: ("Ardra", "good"), 27: ("Kalinash", "good"), 
        28: ("Kshitish", "good"), 29: ("Kamlakara", "good"), 30: ("Gulika", "difficult"), 
        31: ("Mrityu", "difficult"), 32: ("Kaal", "difficult"), 33: ("Davagni", "difficult"), 
        34: ("Ghora", "difficult"), 35: ("Yama", "difficult"), 36: ("Kantaka", "difficult"), 
        37: ("Sudha", "good"), 38: ("Amrita", "good"), 39: ("Purnachandra", "good"), 
        40: ("Vishdagdha", "difficult"), 41: ("Kulanash", "difficult"), 42: ("Vanshakshaya", "difficult"), 
        43: ("Utpaat", "difficult"), 44: ("Kaal", "difficult"), 45: ("Soumya", "good"), 
        46: ("Komala", "good"), 47: ("Sheetala", "good"), 48: ("Drinshtakaral", "difficult"), 
        49: ("Indumukh", "good"), 50: ("Praveena", "good"), 51: ("Kalagni", "difficult"), 
        52: ("Dandayudh", "difficult"), 53: ("Nirmala", "good"), 54: ("Soumya", "good"), 
        55: ("Krura", "difficult"), 56: ("Atisheetala", "good"), 57: ("Sudha", "good"), 
        58: ("Payodhi", "good"), 59: ("Bhramana", "difficult"), 60: ("Chandrarekha", "good")
    }

    def is_odd_sign(sign: str) -> bool:
        odd_signs = {"Ari", "Gem", "Leo", "Lib", "Sag", "Aqu"}
        return sign in odd_signs

    def parse_degree(deg_val) -> float:
        if isinstance(deg_val, (int, float)):
            return float(deg_val)
        try:
            if isinstance(deg_val, str) and ":" in deg_val:
                parts = deg_val.split(":")
                deg = float(parts[0])
                min_val = float(parts[1]) if len(parts) > 1 else 0.0
                sec_val = float(parts[2]) if len(parts) > 2 else 0.0
                return deg + (min_val / 60.0) + (sec_val / 3600.0)
            return float(deg_val)
        except Exception:
            return 0.0

    def calculate_shashtiamsha(sign: str, deg_str_or_num) -> str:
        d = parse_degree(deg_str_or_num)
        d = d % 30.0
        part = int(d * 2.0) + 1
        if part > 60:
            part = 60
        elif part < 1:
            part = 1
        if not is_odd_sign(sign):
            part = 61 - part
        deity_name, quality = _deities.get(part, ("Unknown", "unknown"))
        return f"{deity_name} ({quality})"

    birth_time_note = (
        "Birth time provided by user. D60 Shashtiamsha divisional chart requires extremely "
        "accurate birth time (to seconds) — if birth time is approximate, unknown, or off by "
        "even a couple of minutes, D60 positions and deities will shift completely."
    )

    # --- Extract D60 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d60_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D60":
            d60_positions = chart.get("positions", [])
            break

    planet_map = get_d1_planet_map(structured_data)

    # D60 Lagna
    d60_asc = next(
        (p for p in d60_positions if p.get("planet") == "Ascendant"), {}
    )
    d60_lagna_sign = d60_asc.get("sign", "N/A")
    d60_lagna_lord = _sign_lords.get(d60_lagna_sign, "N/A")
    
    # Calculate lagna shashtiamsha based on D1 Ascendant
    d1_asc = planet_map.get("Ascendant", {})
    d1_asc_sign = d1_asc.get("sign", "Ari")
    d1_asc_deg = d1_asc.get("degree", 0.0)
    d60_lagna_shashtiamsha = calculate_shashtiamsha(d1_asc_sign, d1_asc_deg)
    d60_lagna_str = f"{d60_lagna_sign} (Lord: {d60_lagna_lord}) | Shashtiamsha: {d60_lagna_shashtiamsha}"

    # D60 house lords
    d60_planet_map = {p.get("planet"): p for p in d60_positions}
    d60_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d60_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d60_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d60_lagna_idx = _SIGN_ORDER.index(d60_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d60_house = ((lord_sign_idx - d60_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d60_house = "N/A"
        
        d1_lord_data = planet_map.get(lord_name, {})
        d1_lord_sign = d1_lord_data.get("sign", "Ari")
        d1_lord_deg = d1_lord_data.get("degree", 0.0)
        lord_shashtiamsha = calculate_shashtiamsha(d1_lord_sign, d1_lord_deg)
        
        d60_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D60 House {lord_d60_house} ({lord_sign})"
            f" | Lord Shashtiamsha: {lord_shashtiamsha}"
        )
    d60_house_lords_str = "\n".join(d60_house_lord_lines)

    # D60 planetary placements
    d60_planet_lines = []
    for p in d60_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d60_lagna_idx = _SIGN_ORDER.index(d60_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d60_house_num = ((p_sign_idx - d60_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d60_house_num = "N/A"
        
        p_dignity = p.get("dignity", "N/A")
        p_aspects = p.get("aspects", [])
        
        # calculate shashtiamsha based on D1 position
        d1_p = planet_map.get(pname, {})
        d1_p_sign = d1_p.get("sign", "Ari")
        d1_p_deg = d1_p.get("degree", 0.0)
        p_shashtiamsha = calculate_shashtiamsha(d1_p_sign, d1_p_deg)
        
        d60_planet_lines.append(
            f"  {pname} → D60 House: {d60_house_num}"
            f" | Sign: {p_sign}"
            f" | D60 Degree: {p.get('degree', 'N/A')}°"
            f" | Dignity: {p_dignity}"
            f" | Shashtiamsha: {p_shashtiamsha}"
            f" | Aspects: {p_aspects}"
        )
    d60_planets_str = "\n".join(d60_planet_lines) if d60_planet_lines else "Not available"

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")
    
    # build flat list of D1 placements for D1 cross-ref
    d1_planet_lines = []
    for bp in birth_planets:
        bp_name = bp.get("planet", "")
        d1_planet_lines.append(
            f"  {bp_name}: House {bp.get('house', 'N/A')} | Sign: {bp.get('sign', 'N/A')} | Dignity: {bp.get('dignity', 'N/A')}"
        )
    d1_planets_str = "\n".join(d1_planet_lines) if d1_planet_lines else "Not available"
    
    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 Placements:\n{d1_planets_str}"
    )

    # --- Dasha ---
    dasha_raw = structured_data.get("dasha", {})
    current = dasha_raw.get("data", {}).get("current_period", {})
    mahadasha_str = (
        f"{current.get('mahadasha', 'N/A')}"
        f" (ends: {current.get('mahadasha_end', 'N/A')})"
    )
    antardasha_str = (
        f"{current.get('antardasha', 'N/A')}"
        f" (ends: {current.get('antardasha_end', 'N/A')})"
    )
    antardashas = dasha_raw.get("data", {}).get("current_antardashas", [])
    dasha_seq_lines = []
    for a in antardashas:
        marker = " (CURRENT)" if a.get("is_current") else ""
        dasha_seq_lines.append(
            f"  {a.get('planet')} Antardasha:"
            f" {a.get('start_date')} → {a.get('end_date')}{marker}"
        )
    dasha_sequence_str = (
        "\n".join(dasha_seq_lines) if dasha_seq_lines else "Not available"
    )

    return template.format(
        user_prompt=user_prompt,
        birth_time_note=birth_time_note,
        d60_lagna=d60_lagna_str,
        d60_house_lords=d60_house_lords_str,
        d60_planets=d60_planets_str,
        d1_cross_ref=d1_cross_ref_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
