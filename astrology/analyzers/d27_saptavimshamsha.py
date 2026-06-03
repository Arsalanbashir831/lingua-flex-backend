import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D27_SAPTAVIMSHAMSHA_PROMPT = """
You are an ethical Vedic astrology guide specializing in D27 Saptavimshamsha chart interpretation. Analyze the D27 chart using the provided D1 and D27 planetary details to understand the native's inner strength, resilience, courage, vulnerabilities, fear patterns, endurance, and ability to overcome challenges.

ETHICAL GUIDELINES:
- Do not make fatalistic, fear-based, or absolute predictions about destiny, death, accidents, incurable illness, family separation, or irreversible disaster.
- Do not diagnose medical or psychological conditions.
- Do not make absolute claims about destiny.
- Do not shame the native for difficult placements or create fear about weak planets.
- Avoid extreme or exploitative remedies.
- Use compassionate, respectful, calm, wise, and empowering language.
- Mention uncertainty when birth time accuracy is unclear (divisional charts are sensitive to birth-time errors).
- Emphasize free will, discipline, self-awareness, and conscious action.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}
-----------------------------------

D27 SAPTAVIMSHAMSHA CHART DATA:

D27 Lagna (Ascendant): {d27_lagna}

D27 House Lords (House Sign Lord Where Lord Sits in D27):
{d27_house_lords}

D27 Planetary Placements (with Sign, House, Dignity, and Aspects):
{d27_planets}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE (Physical & General Constitution):
{d1_cross_ref}

-----------------------------------
VIMSHOTTARI DASHA (for timing strength and vulnerability patterns):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D27 KEY PLANETS (Evaluate Each):
- Sun: Willpower, confidence, self-belief, leadership under pressure.
- Moon: Emotional recovery, mental steadiness, sensitivity, inner peace.
- Mars: Courage, action, stamina, fighting spirit, ability to confront challenges.
- Mercury: Adaptability, mental strategy, nervous system tendencies, decision-making under stress.
- Jupiter: Faith, wisdom, protection, optimism, moral strength.
- Venus: Emotional comfort, self-worth, harmony, recovery through love, art, devotion, or relationships.
- Saturn: Endurance, patience, discipline, fear management, maturity through pressure.
- Rahu-Ketu Axis: Rahu shows amplified desire, insecurity, unusual courage, obsession, or pressure. Ketu shows past-life familiarity, detachment, spiritual strength, hidden problem-solving ability, and areas where the person may withdraw.

D27 HOUSE MEANINGS:
1st House: Core courage, physical and psychological resilience, self-belief.
2nd_house: Family conditioning, speech under stress, stored emotional strength, values.
3rd_house: Bravery, effort, initiative, siblings, hands-on courage.
4th_house: Emotional foundation, inner peace, motherly support, comfort patterns.
5th_house: Confidence, intelligence, mantra shakti, past-life merit, creative resilience.
6th_house: Capacity to fight obstacles, competition, illness tendencies, enemies, discipline.
7th_house: Strength through partnerships, cooperation, public interaction.
8th_house: Deep fears, trauma patterns, crisis survival, transformation, occult strength.
9th_house: Faith, blessings, dharma, guru support, divine protection.
10th_house: Responsibility, action under pressure, karma strength, public courage.
11th_house: Support systems, ambition, recovery through community, gains through effort.
12th_house: Subconscious fears, isolation, surrender, spiritual release, hidden strength.

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 13 sections in order:

1. Birth Time and Divisional Chart Accuracy Note
   Assess birth time accuracy and its effect on D27 interpretation. State that divisional charts require accurate birth time.

2. D1 Foundation: Overall Strength and Resilience
   Use the provided D1 chart as the foundation. First assess the native's overall constitution, Lagna, Lagna lord, Moon, Mars, Saturn, Sun, and the strength of key houses.

3. Key D1 Indicators: Lagna, Moon, Mars, Saturn, Sun
   Provide detailed assessment of Lagna/lord (vitality), Moon (stability), Mars (courage), Saturn (patience), Sun (willpower) in D1.

4. D27 Lagna and Lagna Lord
   Analyze the D27 Lagna and D27 Lagna lord by house, sign, dignity, conjunctions, and aspects to understand basic resilience and inner defense mechanism.

5. Planetary Strengths in D27
   Go through D27 planetary strengths for Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn. Explain their subtle inner values.

6. House-by-House D27 Interpretation
   Analyze all 12 D27 houses using the house meanings above. For each house, evaluate: sign, lord, planets present, dignity, aspects.

7. Rahu-Ketu Axis in D27
   Analyze Rahu and Ketu placement in D27 to understand obsessions, hidden problem-solving abilities, and withdrawal points.

8. D1 and D27 Comparison
   Compare each major D1 indication with its D27 counterpart. Assess if planets are strong in both (reliable strength), strong in D1/weak in D27 (outer capacity but inner doubt), weak in D1/strong in D27 (hidden strength emerges), or challenged in both (healing and growth area).

9. Current Dasha Activation
   Explain how the current Mahadasha and Antardasha lords operate in D1 and D27.

10. Core Inner Strengths
    Summarize the native's main strengths (courage, endurance, recovery, discipline, faith, or crisis survival).

11. Sensitive Areas for Growth
    Summarize growth areas using gentle language. Do not label the native as weak.

12. Practical and Spiritual Remedies
    Suggest practical and spiritual remedies based on the challenged planets (discipline, meditation, mantra, charity, physical exercise, breathwork, journaling, therapy).

13. Final Guidance
    Conclude with empowering and spiritually grounded guidance. Emphasize free will, self-awareness, and conscious action.

STYLE: Structured, compassionate, subtle, non-fatalistic, and spiritually mature.
TONE: Calm, ethical, empowering, and grounded.
"""

def build_d27_saptavimshamsha_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    _sign_lords = {
        "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
        "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
        "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
    }

    birth_time_note = (
        "Birth time provided by user. D27 Saptavimshamsha divisional chart requires "
        "accurate birth time — if birth time is approximate or unknown, D27 positions may shift."
    )

    # --- Extract D27 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d27_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D27":
            d27_positions = chart.get("positions", [])
            break

    planet_map = get_d1_planet_map(structured_data)

    # D27 Lagna
    d27_asc = next(
        (p for p in d27_positions if p.get("planet") == "Ascendant"), {}
    )
    d27_lagna_sign = d27_asc.get("sign", "N/A")
    d27_lagna_lord = _sign_lords.get(d27_lagna_sign, "N/A")
    d27_lagna_str = f"{d27_lagna_sign} (Lord: {d27_lagna_lord})"

    # D27 house lords
    d27_planet_map = {p.get("planet"): p for p in d27_positions}
    d27_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d27_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d27_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d27_lagna_idx = _SIGN_ORDER.index(d27_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d27_house = ((lord_sign_idx - d27_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d27_house = "N/A"
        
        d27_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D27 House {lord_d27_house} ({lord_sign})"
        )
    d27_house_lords_str = "\n".join(d27_house_lord_lines)

    # D27 planetary placements
    d27_planet_lines = []
    for p in d27_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d27_lagna_idx = _SIGN_ORDER.index(d27_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d27_house_num = ((p_sign_idx - d27_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d27_house_num = "N/A"
        
        p_dignity = p.get("dignity", "N/A")
        p_aspects = p.get("aspects", [])
        
        d27_planet_lines.append(
            f"  {pname} → D27 House: {d27_house_num}"
            f" | Sign: {p_sign}"
            f" | D27 Degree: {p.get('degree', 'N/A')}°"
            f" | Dignity: {p_dignity}"
            f" | Aspects: {p_aspects}"
        )
    d27_planets_str = "\n".join(d27_planet_lines) if d27_planet_lines else "Not available"

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")
    bp_map = {p.get("planet"): p for p in birth_planets}

    d1_3rd_lord = _d1_lord_of_house(3)
    d1_6th_lord = _d1_lord_of_house(6)
    d1_8th_lord = _d1_lord_of_house(8)
    d1_12th_lord = _d1_lord_of_house(12)

    def _planet_summary(planet_name: str) -> str:
        p = bp_map.get(planet_name, {})
        return (
            f"House {p.get('house', 'N/A')}"
            f" | Sign: {p.get('sign', 'N/A')} ({p.get('dignity', 'N/A')})"
        )

    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 Sun (Willpower) — {_planet_summary('Sun')}\n"
        f"  D1 Moon (Mind/Emotion) — {_planet_summary('Moon')}\n"
        f"  D1 Mars (Courage/Resilience) — {_planet_summary('Mars')}\n"
        f"  D1 Saturn (Endurance/Fear) — {_planet_summary('Saturn')}\n"
        f"  D1 3rd House Lord (Effort): {d1_3rd_lord} — {_planet_summary(d1_3rd_lord)}\n"
        f"  D1 6th House Lord (Obstacles): {d1_6th_lord} — {_planet_summary(d1_6th_lord)}\n"
        f"  D1 8th House Lord (Crisis): {d1_8th_lord} — {_planet_summary(d1_8th_lord)}\n"
        f"  D1 12th House Lord (Vulnerabilities): {d1_12th_lord} — {_planet_summary(d1_12th_lord)}"
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
        d27_lagna=d27_lagna_str,
        d27_house_lords=d27_house_lords_str,
        d27_planets=d27_planets_str,
        d1_cross_ref=d1_cross_ref_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
