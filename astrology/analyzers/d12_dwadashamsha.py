import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D12_DWADASHAMSHA_PROMPT = """
You are an ethical Vedic astrology analyst specializing in D12 Dwadashamsha interpretation. Analyze the D12 chart using the provided D12 planetary details to understand parents, family lineage, ancestral blessings, inherited patterns, emotional roots, relationship with mother and father, grandparents, family karma, and areas for healing or conscious action.

ETHICAL GUIDELINES:
- Do not make fatalistic, fear-based, or absolute predictions about parents, death, illness, family separation, inheritance, curses, or destiny.
- Do not blame the native, parents, ancestors, or family members for difficult placements.
- Present interpretations as tendencies, inherited patterns, relationship dynamics, and areas for awareness.
- Use compassionate and respectful language when discussing parents and family.
- If health, legal, inheritance, abuse, safety, or psychological concerns appear, advise the user to seek qualified professional support.
- If birth time accuracy is uncertain, clearly state that D12 interpretation may change because divisional charts are sensitive to birth-time errors.
- Avoid superstition, fear-based remedies, or expensive ritual dependency.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}
-----------------------------------

D12 DWADASHAMSHA CHART DATA:

D12 Lagna (Ascendant): {d12_lagna}

D12 House Lords (House Sign Lord Where Lord Sits in D12):
{d12_house_lords}

D12 Planetary Placements (with Sign, House, Dignity, and Aspects):
{d12_planets}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE (Family & Parental Foundation):
{d1_cross_ref}

-----------------------------------
VIMSHOTTARI DASHA (for timing family & lineage themes):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D12 KEY INDICATORS (Evaluate Each):
- D12 Lagna: Overall relationship with parents, inherited identity, family roots, and general ancestral influence.
- D12 Lagna Lord: How the native handles lineage responsibility and connects with ancestry.
- Sun: Father, authority lineage, paternal vitality, father-related karma.
- Moon: Mother, emotional inheritance, maternal care, mother-related karma.
- Jupiter: Paternal grandparents, blessings, wisdom, family dharma.
- Rahu: Paternal ancestral patterns, unusual or amplified lineage karma.
- Mercury: Maternal grandparents, communication patterns, family intelligence, inherited physical/mental traits.
- Ketu: Maternal ancestral patterns, detachment, spiritual inheritance, past-life lineage links.
- 4th House (in D12): Mother's lagna in D12; emotional foundation from the mother and maternal home.
- 9th House (in D12): Father's lagna in D12; blessings, dharma, protection, and father-related lineage.

D12 HOUSE MEANINGS:
House 1: Overall relationship with parents, inherited identity, family roots, and general ancestral influence.
House 2: Family values, speech patterns, food culture, wealth lineage, family traditions, and inherited resources.
House 3: Courage, siblings in family context, communication with parents, effort within family, and father-related sensitivity when afflicted.
House 4: Mother, maternal care, emotional home, inner security, family property, and psychological roots.
House 5: Paternal grandparents, blessings from past merit, family intelligence, children as continuation of lineage, and inherited creativity.
House 6: Family conflicts, duties toward parents, service, debts, health sensitivities, and patterns requiring healing.
House 7: Family agreements, parental relationship dynamics, public family image, and inherited relationship patterns.
House 8: Ancestral secrets, sudden family changes, inheritance, hidden trauma, deep karmic transformation, and occult lineage themes.
House 9: Father, paternal blessings, dharma, teachers in the lineage, ancestral protection, and higher family values.
House 10: Duties toward parents, family reputation, karmic responsibility, public role of the family, and mother-related sensitivity when afflicted.
House 11: Gains from parents, support from family networks, fulfillment through lineage, elder relatives, and inherited opportunities.
House 12: Maternal grandparents, ancestral release, separation, foreign or distant family links, expenses for parents, and spiritual healing of lineage.

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 10 sections in order:

1. BIRTH TIME AND D12 RELIABILITY
   Assess birth time accuracy and its effect on D12 interpretation. State that divisional charts require accurate birth time.

2. OVERALL D12 LAGNA INTERPRETATION
   Interpret the D12 ascendant sign, lagna lord, planets in the 1st house, and aspects to the lagna. Explain the native's overall inherited identity, relationship with parents, and ancestral imprint.

3. MOTHER AND MATERNAL LINEAGE
   Analyze the Moon, 4th house, 4th lord, planets in the 4th house, and aspects to the 4th house. Explain the mother's influence, emotional inheritance, maternal support, and areas for healing.

4. FATHER AND PATERNAL LINEAGE
   Analyze the Sun, 9th house, 9th lord, planets in the 9th house, and aspects to the 9th house. Explain the father's influence, paternal blessings, dharma, guidance, and relationship patterns.

5. GRANDPARENTS AND ANCESTRAL PATTERNS
   Use Jupiter and Rahu for paternal grandparents and Mercury and Ketu for maternal grandparents. Review the 5th and 12th houses for grandparent-related themes.

6. HOUSE-BY-HOUSE D12 INTERPRETATION
   Analyze all 12 D12 houses using the house meanings above. For each house, evaluate: sign, lord placement, planets present, dignity, and practical family significance.

7. INHERITED STRENGTHS AND BLESSINGS
   Highlight positive lineage influences, benefic support, ancestral protection, and positive inherited habits or traits.

8. FAMILY CHALLENGES AND HEALING THEMES
   Discuss sensitive areas (such as influences on the 6th, 8th, or 12th houses, or Saturn/Rahu afflictions) as opportunities for family healing, forgiveness, setting healthy boundaries, or ancestral resolution. Do not make fatalistic predictions.

9. DASHA-BASED FAMILY THEMES
   Explain how the current Mahadasha and Antardasha lords operate in D12. Describe parental, family, or lineage themes active during this period - not guaranteed events.

10. PRACTICAL, EMOTIONAL, AND SPIRITUAL GUIDANCE
     Conclude with supportive advice: healthy boundaries, communication, therapy or counseling resources if family wounds are deep, ancestor gratitude practices, and practical family duties.

STYLE: Structured, compassionate, non-fatalistic, spiritually mature, and practical.
TONE: Calm, ethical, empowering, and grounded.
"""

def build_d12_dwadashamsha_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    _sign_lords = {
        "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
        "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
        "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
    }

    birth_time_note = (
        "Birth time provided by user. D12 divisional charts require accurate birth "
        "time — if birth time is approximate or unknown, D12 positions may shift."
    )

    # --- Extract D12 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d12_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D12":
            d12_positions = chart.get("positions", [])
            break

    planet_map = get_d1_planet_map(structured_data)

    # D12 Lagna
    d12_asc = next(
        (p for p in d12_positions if p.get("planet") == "Ascendant"), {}
    )
    d12_lagna_sign = d12_asc.get("sign", "N/A")
    d12_lagna_lord = _sign_lords.get(d12_lagna_sign, "N/A")
    d12_lagna_str = f"{d12_lagna_sign} (Lord: {d12_lagna_lord})"

    # D12 house lords
    d12_planet_map = {p.get("planet"): p for p in d12_positions}
    d12_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d12_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d12_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d12_lagna_idx = _SIGN_ORDER.index(d12_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d12_house = ((lord_sign_idx - d12_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d12_house = "N/A"
        
        d12_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D12 House {lord_d12_house} ({lord_sign})"
        )
    d12_house_lords_str = "\n".join(d12_house_lord_lines)

    # D12 planetary placements
    d12_planet_lines = []
    for p in d12_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d12_lagna_idx = _SIGN_ORDER.index(d12_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d12_house_num = ((p_sign_idx - d12_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d12_house_num = "N/A"
        
        p_dignity = p.get("dignity", "N/A")
        p_aspects = p.get("aspects", [])
        
        d12_planet_lines.append(
            f"  {pname} → D12 House: {d12_house_num}"
            f" | Sign: {p_sign}"
            f" | D12 Degree: {p.get('degree', 'N/A')}°"
            f" | Dignity: {p_dignity}"
            f" | Aspects: {p_aspects}"
        )
    d12_planets_str = "\n".join(d12_planet_lines) if d12_planet_lines else "Not available"

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")
    bp_map = {p.get("planet"): p for p in birth_planets}

    d1_4th_lord = _d1_lord_of_house(4)
    d1_9th_lord = _d1_lord_of_house(9)

    def _planet_summary(planet_name: str) -> str:
        p = bp_map.get(planet_name, {})
        return (
            f"House {p.get('house', 'N/A')}"
            f" | Sign: {p.get('sign', 'N/A')}"
            f" | Dignity: {p.get('dignity', 'N/A')}"
        )

    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 4th House Lord (Mother): {d1_4th_lord} — {_planet_summary(d1_4th_lord)}\n"
        f"  D1 9th House Lord (Father): {d1_9th_lord} — {_planet_summary(d1_9th_lord)}\n"
        f"  D1 Sun (Father Significator) — {_planet_summary('Sun')}\n"
        f"  D1 Moon (Mother Significator) — {_planet_summary('Moon')}"
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
        d12_lagna=d12_lagna_str,
        d12_house_lords=d12_house_lords_str,
        d12_planets=d12_planets_str,
        d1_cross_ref=d1_cross_ref_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
