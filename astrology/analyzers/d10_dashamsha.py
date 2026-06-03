import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D10_DASHAMSHA_PROMPT = """
You are an ethical Vedic astrology analyst specializing in D10 Dashamsha career interpretation. Analyze the D10 chart using the provided D1 and D10 planetary details to understand career, profession, status, work karma, professional growth, and one's role in society.

ETHICAL GUIDELINES:
- Do not make fatalistic or fear-based predictions about career failure, job loss, poverty, or legal/professional disputes.
- Do not guarantee career success, promotion, wealth accumulation, fame, or specific outcomes.
- Present interpretations as tendencies, strengths, challenges, and areas for conscious action.
- For business investments, legal contracts, employment disputes, or financial planning, advise consulting qualified professionals.
- Use compassionate, respectful, and practical language.
- If birth time accuracy is uncertain, clearly state that D10 interpretation may change because divisional charts are highly sensitive to birth-time errors.
- Avoid superstition, fear-based remedies, or expensive ritual dependency.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}
-----------------------------------

D10 DASHAMSHA CHART DATA:

D10 Lagna (Ascendant): {d10_lagna}

D10 House Lords (House Sign Lord Where Lord Sits in D10):
{d10_house_lords}

D10 Planetary Placements (with Sign, House, Dignity, and Aspects):
{d10_planets}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE (Career Foundation):
{d1_cross_ref}

Jaimini Career Indicators:
- Atmakaraka (AK): {atmakaraka}
- Amatyakaraka (AmK): {amatyakaraka}

-----------------------------------
VIMSHOTTARI DASHA (for timing professional themes):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D10 CORE INDICATORS (Evaluate Each):
- D10 Lagna: Overall career identity, approach to work, professional temperament, and aptitude.
- D10 Lagna Lord: How the native pursues, manages, and executes their career path and responsibilities.
- D10 10th House & Lord: Status, authority, career visibility, main career direction, and public reputation.
- Sun in D10: Leadership, authority, recognition, relationship with government/superiors, self-expression in career.
- Moon in D10: Professional satisfaction, public connection, emotional stability in work environment, adaptation.
- Mars in D10: Drive, ambition, competition, initiative, technical/engineering skills, conflicts or leadership style.
- Mercury in D10: Communication, analytical skills, trade, business, writing, teaching, intelligence in execution.
- Jupiter in D10: Wisdom, guidance, advisory roles, ethics, expansion, protection, counseling, professional growth.
- Venus in D10: Creativity, diplomacy, luxury industries, design, media, public relations, relationship with colleagues.
- Saturn in D10: Discipline, service, patience, delay, structure, administrative roles, hard work, and responsibility.
- Rahu in D10: Unconventional career paths, foreign links, rapid growth, speculation, tech/innovative industries.
- Ketu in D10: Behind-the-scenes roles, spiritual work, detachment from status, analytical/meticulous detail.

D10 HOUSE MEANINGS:
House 1: Overall career karma, professional identity, aptitude, work personality, initial approach to work.
House 2: Resources for work, income through profession, support system, family support, speech and value creation in career.
House 3: Effort, courage, productivity, communication, creativity, skills, initiative, practical decision-making.
House 4: Comfort and happiness from work, work environment, emotional satisfaction, possibility of working from home or stable base.
House 5: Professional intelligence, strategy, creativity, learning, advisory ability, mindset toward work.
House 6: Competition, service, employment, discipline, conflicts, ability to overcome rivals, ethics in daily work.
House 7: Public dealing, clients, business partnerships, marketplace, professional visibility through others.
House 8: Sudden changes, hidden work, research, instability, transformation, crisis-handling, unconventional income patterns.
House 9: Fortune in career, mentors, dharma in profession, higher guidance, ethics, blessings from teachers or institutions.
House 10: Main karma, status, authority, leadership, career rise, responsibility, recognition, professional role.
House 11: Gains from work, networks, awards, promotions, fulfillment of career ambitions, income expansion.
House 12: Professional expenditure, foreign connections, isolation, behind-the-scenes work, losses, surrender, spiritualization of work.

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 11 sections in order:

1. BIRTH TIME AND D10 RELIABILITY
   Assess birth time accuracy and its effect on D10 interpretation. Note that D10 is highly sensitive to birth time errors.

2. D1 CAREER FOUNDATION
   Summarize career foundation from D1: D1 Lagna/lord, D1 10th house/lord, Sun (status), Saturn (service/work). Explain how these set the baseline potential.

3. D10 LAGNA ANALYSIS
   Interpret D10 ascendant sign, lagna lord, and planets in the 1st house. Explain professional temperament, career identity, and approach to work.

4. D10 10TH HOUSE AND 10TH LORD ANALYSIS
   Interpret the 10th house in D10, the 10th lord, planets placed there, aspects, and dignity. Discuss status, authority, recognition, and main career direction.

5. HOUSE-BY-HOUSE D10 INTERPRETATION
   Analyze all 12 D10 houses using the house meanings above. For each house, evaluate: sign, lord, planets present, dignity, and practical career significance.

6. D1-D10 REPEATED THEMES
   Evaluate which career indicators and themes repeat across D1 and D10 (e.g., strong Saturn, Jupiter influence, similar 10th lords, or Jaimini AK/AmK themes).

7. STRENGTHS AND CAREER GIFTS
   Identify the primary career strengths, natural talents, potential for leadership, business aptitude, or service dedication.

8. CHALLENGES AND CONSCIOUS CORRECTIONS
   Discuss career obstacles, relationship with authority figures, workplace conflicts, periods of instability, or ethical temptations. Frame these as lessons for conscious growth.

9. SUITABLE CAREER DIRECTIONS
   Synthesize the findings to suggest specific professional fields (e.g., management, technology, public service, entrepreneurship, arts, advisory/counseling) and working styles (service vs. business).

10. DASHA-BASED CAREER TIMING
     Explain how the current Mahadasha and Antardasha lords operate in D10. Describe active professional themes, opportunities, and cautions during this period.

11. PRACTICAL AND ETHICAL GUIDANCE
     Conclude with practical, actionable career advice: skills to focus on, behavioral habits to cultivate, ethical values, and professional planning guidance.

STYLE: Structured, practical, compassionate, non-fatalistic, and clear.
TONE: Calm, ethical, empowering, and grounded.
"""

def build_d10_dashamsha_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
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
        "Birth time provided by user. D10 divisional charts require accurate birth "
        "time — if birth time is approximate or unknown, D10 positions may shift."
    )

    # --- Extract D10 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d10_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D10":
            d10_positions = chart.get("positions", [])
            break

    planet_map = get_d1_planet_map(structured_data)

    # D10 Lagna
    d10_asc = next(
        (p for p in d10_positions if p.get("planet") == "Ascendant"), {}
    )
    d10_lagna_sign = d10_asc.get("sign", "N/A")
    d10_lagna_lord = _sign_lords.get(d10_lagna_sign, "N/A")
    d10_lagna_str = f"{d10_lagna_sign} (Lord: {d10_lagna_lord})"

    # D10 house lords
    d10_planet_map = {p.get("planet"): p for p in d10_positions}
    d10_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d10_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d10_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d10_lagna_idx = _SIGN_ORDER.index(d10_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d10_house = ((lord_sign_idx - d10_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d10_house = "N/A"
        
        d10_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D10 House {lord_d10_house} ({lord_sign})"
        )
    d10_house_lords_str = "\n".join(d10_house_lord_lines)

    # D10 planetary placements
    d10_planet_lines = []
    for p in d10_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d10_lagna_idx = _SIGN_ORDER.index(d10_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d10_house_num = ((p_sign_idx - d10_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d10_house_num = "N/A"
        
        p_dignity = p.get("dignity", "N/A")
        p_aspects = p.get("aspects", [])
        
        d10_planet_lines.append(
            f"  {pname} → D10 House: {d10_house_num}"
            f" | Sign: {p_sign}"
            f" | D10 Degree: {p.get('degree', 'N/A')}°"
            f" | Dignity: {p_dignity}"
            f" | Aspects: {p_aspects}"
        )
    d10_planets_str = "\n".join(d10_planet_lines) if d10_planet_lines else "Not available"

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")
    bp_map = {p.get("planet"): p for p in birth_planets}

    d1_10th_lord = _d1_lord_of_house(10)

    def _planet_summary(planet_name: str) -> str:
        p = bp_map.get(planet_name, {})
        return (
            f"House {p.get('house', 'N/A')}"
            f" | Sign: {p.get('sign', 'N/A')}"
            f" | Dignity: {p.get('dignity', 'N/A')}"
        )

    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 10th House Lord: {d1_10th_lord} — {_planet_summary(d1_10th_lord)}\n"
        f"  D1 Sun (Significator of Career/Status) — {_planet_summary('Sun')}\n"
        f"  D1 Saturn (Significator of Work/Service) — {_planet_summary('Saturn')}"
    )

    # Calculate AK and AmK (7-karaka scheme)
    seven_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    planet_degrees_list = []
    for pname in seven_planets:
        p_d1 = planet_map.get(pname, {})
        deg_val = parse_degree(p_d1.get("degree", 0.0))
        planet_degrees_list.append((pname, deg_val))
    
    planet_degrees_list.sort(key=lambda x: x[1], reverse=True)
    ak_planet = planet_degrees_list[0][0] if len(planet_degrees_list) > 0 else "N/A"
    ak_degree = planet_degrees_list[0][1] if len(planet_degrees_list) > 0 else 0.0
    amk_planet = planet_degrees_list[1][0] if len(planet_degrees_list) > 1 else "N/A"
    amk_degree = planet_degrees_list[1][1] if len(planet_degrees_list) > 1 else 0.0
    
    atmakaraka_str = f"{ak_planet} ({ak_degree:.2f}°)"
    amatyakaraka_str = f"{amk_planet} ({amk_degree:.2f}°)"

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
        d10_lagna=d10_lagna_str,
        d10_house_lords=d10_house_lords_str,
        d10_planets=d10_planets_str,
        d1_cross_ref=d1_cross_ref_str,
        atmakaraka=atmakaraka_str,
        amatyakaraka=amatyakaraka_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
