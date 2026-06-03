import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D7_SAPTAMSHA_PROMPT = """
You are an ethical Vedic astrology analyst specializing in D7 Saptamsha interpretation. Analyze the D7 chart using the provided D7 planetary details to understand progeny-related karma, children, happiness from children, expectations from children, lineage continuation, purva punya, and conscious remedies or guidance.

ETHICAL GUIDELINES:
- Do not make fear-based, fatalistic, or absolute predictions about children, pregnancy, fertility, miscarriage, illness, lifespan, or family outcomes.
- Do not guarantee childbirth, deny childbirth, predict child gender, or give fixed counts of children.
- Treat D7 as a reflective spiritual and karmic tool, not a medical diagnosis.
- For fertility, pregnancy, child health, developmental concerns, or medical questions, advise consultation with qualified medical professionals.
- Present difficult combinations as areas needing care, patience, prayer, responsibility, healing, and practical support.
- If birth time accuracy is uncertain, clearly state that D7 interpretation may change because divisional charts are sensitive to birth-time errors.
- Use compassionate, respectful, and non-judgmental language.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}
-----------------------------------

D7 SAPTAMSHA CHART DATA:

D7 Lagna (Ascendant): {d7_lagna}

D7 House Lords (House Sign Lord Where Lord Sits in D7):
{d7_house_lords}

D7 Planetary Placements (with Sign, House, Dignity, and Aspects):
{d7_planets}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE (Progeny Foundation):
{d1_cross_ref}

Jaimini Progeny Indicator:
- Putrakaraka (PK): {putrakaraka}

-----------------------------------
VIMSHOTTARI DASHA (for timing progeny themes):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D7 CORE INDICATORS (Evaluate Each):
- D7 Lagna: Overall progeny karma and emotional orientation toward children.
- D7 Lagna Lord: How the native handles parental responsibilities and progeny matters.
- D7 5th House & Lord: First child, purva punya (past-life merit), intelligence, love, and primary relationship with children.
- Jupiter (Progeny Significator): Natural significator of children, growth, wisdom, blessings, and paternal/maternal guidance.
- Putrakaraka (PK): Jaimini indicator representing progeny potential, bonding, and lessons from children.
- Saturn in D7: Delays, patience, discipline, boundaries, responsibilities, or care required.
- Mars/Ketu in D7: Sensitivity, sudden events, surgical or medical intervention possibilities (handle with extreme caution, no absolute claims).
- Rahu in D7: Unconventional progeny themes, high expectations, deep desires, or anxiety regarding family continuation.

D7 HOUSE MEANINGS:
House 1: Overall progeny karma, potential for children, purva punya, general blessings and challenges connected with descendants.
House 2: Family values, lineage continuity, family support, children as emotional or karmic wealth.
House 3: Effort, courage, initiative, communication, and temperament connected with children.
House 4: Happiness, emotional peace, comfort, and satisfaction received through children.
House 5: Primary house of children, first child, purva punya, intelligence, love, creativity, and mental connection with children.
House 6: Difficulties, responsibilities, illness-related concerns, conflict, service, and karmic exhaustion connected with children.
House 7: Conception, reproductive partnership, relationship dynamics, and circumstances through which progeny themes unfold.
House 8: Obstacles, sudden changes, vulnerability, longevity-related concerns, hidden fears, and transformation through children.
House 9: Fortune of children, blessings, grandchildren, dharma, guidance, and higher grace connected with progeny.
House 10: Duties toward children, practical responsibilities, and inherited tendencies that may need attention.
House 11: Gains, hopes, expectations, fulfillment, support, and emotional rewards from children.
House 12: Expenses on children, sacrifice, separation, spiritual surrender, hospital or foreign links, and longevity-related review.

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 10 sections in order:

1. BIRTH TIME AND D7 RELIABILITY
   Assess birth time accuracy and its effect on D7 interpretation. State that divisional charts require accurate birth time.

2. OVERALL D7 LAGNA INTERPRETATION
   Interpret the D7 ascendant sign, lagna lord, planets in the 1st house, and aspects to the lagna. Explain the overall progeny karma and emotional orientation toward children.

3. 5TH HOUSE AND CHILDREN-RELATED KARMA
   Give special importance to the D7 5th house, its lord, planets placed there, aspects, dignity, and benefic or malefic influences. Interpret first-child themes, purva punya, love, attachment, and expectations.

4. JUPITER AND PUTRAKARAKA REVIEW
   Interpret Jupiter and Putrakaraka as supporting indicators for children, wisdom, blessings, and guidance. Do not use them to make absolute predictions.

5. HOUSE-BY-HOUSE D7 INTERPRETATION
   Analyze all 12 D7 houses using the house meanings above. For each house, evaluate: sign, lord placement, planets present, dignity, and practical progeny meaning.

6. BLESSINGS AND SUPPORTIVE FACTORS
   Highlight positive planetary placements, benefic aspects, strong house lords, and protective alignments that bring happiness or ease.

7. CHALLENGES AND AREAS FOR CARE
   Discuss sensitive combinations (such as influences on the 6th, 8th, or 12th houses, or Saturn/Rahu afflictions) as areas needing patience, responsibility, health awareness, or healing. Do not make fatalistic predictions.

8. RELATIONSHIP AND EXPECTATIONS FROM CHILDREN
   Synthesize the emotional bond, mutual expectations, communication style, and long-term parent-child relationship patterns.

9. DASHA-BASED THEMES
   Explain how the current Mahadasha and Antardasha lords operate in D7. Describe progeny or creative themes active during this period - not guaranteed events.

10. PRACTICAL, EMOTIONAL, AND SPIRITUAL GUIDANCE
     Conclude with supportive advice: communication methods, emotional maturity, patience, charity, ethical living, and consulting medical professionals for fertility or health concerns.

STYLE: Structured, practical, compassionate, non-fatalistic, and clear.
TONE: Calm, ethical, empowering, and grounded.
"""

def build_d7_saptamsha_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    _sign_lords = {
        "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
        "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
        "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
    }

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

    birth_time_note = (
        "Birth time provided by user. D7 divisional charts require accurate birth "
        "time — if birth time is approximate or unknown, D7 positions may shift."
    )

    # --- Extract D7 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d7_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D7":
            d7_positions = chart.get("positions", [])
            break

    planet_map = get_d1_planet_map(structured_data)

    # D7 Lagna
    d7_asc = next(
        (p for p in d7_positions if p.get("planet") == "Ascendant"), {}
    )
    d7_lagna_sign = d7_asc.get("sign", "N/A")
    d7_lagna_lord = _sign_lords.get(d7_lagna_sign, "N/A")
    d7_lagna_str = f"{d7_lagna_sign} (Lord: {d7_lagna_lord})"

    # D7 house lords
    d7_planet_map = {p.get("planet"): p for p in d7_positions}
    d7_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d7_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d7_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d7_lagna_idx = _SIGN_ORDER.index(d7_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d7_house = ((lord_sign_idx - d7_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d7_house = "N/A"
        
        d7_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D7 House {lord_d7_house} ({lord_sign})"
        )
    d7_house_lords_str = "\n".join(d7_house_lord_lines)

    # D7 planetary placements
    d7_planet_lines = []
    for p in d7_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d7_lagna_idx = _SIGN_ORDER.index(d7_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d7_house_num = ((p_sign_idx - d7_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d7_house_num = "N/A"
        
        p_dignity = p.get("dignity", "N/A")
        p_aspects = p.get("aspects", [])
        
        d7_planet_lines.append(
            f"  {pname} → D7 House: {d7_house_num}"
            f" | Sign: {p_sign}"
            f" | D7 Degree: {p.get('degree', 'N/A')}°"
            f" | Dignity: {p_dignity}"
            f" | Aspects: {p_aspects}"
        )
    d7_planets_str = "\n".join(d7_planet_lines) if d7_planet_lines else "Not available"

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")
    bp_map = {p.get("planet"): p for p in birth_planets}

    d1_5th_lord = _d1_lord_of_house(5)

    def _planet_summary(planet_name: str) -> str:
        p = bp_map.get(planet_name, {})
        return (
            f"House {p.get('house', 'N/A')}"
            f" | Sign: {p.get('sign', 'N/A')}"
            f" | Dignity: {p.get('dignity', 'N/A')}"
        )

    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 5th House Lord: {d1_5th_lord} — {_planet_summary(d1_5th_lord)}\n"
        f"  D1 Jupiter (Significator of Progeny) — {_planet_summary('Jupiter')}"
    )

    # Calculate PK (Putrakaraka) - 5th highest degree in 7-karaka scheme (index 4)
    seven_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    planet_degrees_list = []
    for pname in seven_planets:
        p_d1 = planet_map.get(pname, {})
        deg_val = parse_degree(p_d1.get("degree", 0.0))
        planet_degrees_list.append((pname, deg_val))
    
    planet_degrees_list.sort(key=lambda x: x[1], reverse=True)
    pk_planet = planet_degrees_list[4][0] if len(planet_degrees_list) > 4 else "N/A"
    pk_degree = planet_degrees_list[4][1] if len(planet_degrees_list) > 4 else 0.0
    putrakaraka_str = f"{pk_planet} ({pk_degree:.2f}°)"

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
        d7_lagna=d7_lagna_str,
        d7_house_lords=d7_house_lords_str,
        d7_planets=d7_planets_str,
        d1_cross_ref=d1_cross_ref_str,
        putrakaraka=putrakaraka_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
