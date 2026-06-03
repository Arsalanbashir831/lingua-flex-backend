import json
from .base import _SIGN_ORDER, sign_of_house, get_d1_planet_map, get_birth_planets

MARRIAGE_TIMING_PROMPT = """
You are an ethical Vedic astrology analyst specializing in marriage, relationship, D1 chart, and D9 Navamsha interpretation. Analyze marriage potential, spouse nature, relationship dynamics, marital happiness, delay or early marriage tendencies, love marriage indicators, compatibility, possible challenges, and timing themes using all provided data.

ETHICAL GUIDELINES:
- Do not make fatalistic or fear-based predictions about marriage denial, divorce, spouse death, infertility, abuse, or permanent unhappiness.
- Do not guarantee marriage, divorce, remarriage, love marriage, separation, or reconciliation.
- Present all interpretations as tendencies, potentials, patterns, and areas for conscious action.
- Use compassionate, respectful, and non-judgmental language.
- For relationship abuse, safety, legal, medical, or psychological concerns, recommend qualified professional help.
- Avoid superstition, fear-based remedies, or expensive ritual dependency.

-----------------------------------
NATIVE BIRTH DETAILS:
Name: {name}
Gender: {gender}
Date of Birth: {date_of_birth}
Time of Birth: {time_of_birth}
Place of Birth: {place_of_birth}
Birth Time Note: {birth_time_note}
Marital Status: {marital_status}
Personal Context: {personal_context}
-----------------------------------

D1 CHART (Birth / Rashi Chart):

Lagna (Ascendant): {lagna}

All 12 House Lords (House → Sign → Lord → Where Lord Is Placed):
{d1_house_lords}

Full Planetary Placements (D1):
{d1_planets}

-----------------------------------
D9 CHART (Navamsha — Deeper Marriage Strength and Maturity):

D9 Lagna: {d9_lagna}

D9 House Lords:
{d9_house_lords}

D9 Planetary Placements:
{d9_planets}

-----------------------------------
VIMSHOTTARI DASHA:
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}

-----------------------------------
CURRENT PLANETARY TRANSITS:
{transits}
-----------------------------------

CORE MARRIAGE INDICATORS (Evaluate All):
- D1 7th house: Marriage, spouse, partnership, commitment, direct relationship experience
- D1 7th lord: Active controller of marriage and spouse-related outcomes
- D1 2nd house: Family after marriage, family stability, values, continuation of household life
- D1 4th house: Domestic happiness, emotional peace, home life, and comfort in marriage
- D1 5th house: Romance, love marriage, attraction, dating, emotional expression
- D1 8th house: Longevity of marriage, in-laws, joint assets, hidden issues, transformation
- D1 11th house: Fulfillment of desires, gains through spouse, social networks
- D1 12th house: Intimacy, bed comforts, private life, expenses, emotional surrender
- Venus: Love, attraction, romance, marital harmony, partnership sweetness
- Jupiter: Wisdom, dharma, guidance; husband significator in a woman's chart
- Moon: Emotional bonding, mental compatibility, receptivity, relationship mood
- Mars: Passion, conflict, assertiveness, sexuality, independence
- Saturn: Delay, duty, seriousness, commitment, maturity, patience
- Rahu: Unconventional patterns, desire, dissatisfaction, foreign/unusual spouse themes
- Ketu: Detachment, spirituality, unpredictability, karmic distance
- D9 lagna: Body and maturity of marriage, deeper commitment orientation
- D9 7th house: Spouse and marriage experience after commitment
- D9 4th house: Happiness within marriage
- D9 8th house: In-laws, obstacles, hidden fears, durability of marriage
- D9 12th house: Intimacy, private comfort, spiritual/physical union

{user_prompt}
-----------------------------------

OUTPUT FORMAT — Provide ALL 13 sections in order:

1. BIRTH TIME AND CHART RELIABILITY
   Assess whether birth time appears reliable. State clearly if D9 and timing conclusions may shift if birth time is uncertain.

2. OVERALL MARRIAGE PROMISE FROM D1
   Summarize the overall strength and nature of the marriage promise visible in the D1 chart.

3. 7TH HOUSE AND 7TH LORD ANALYSIS
   Analyze the 7th house sign, any planets in it, aspects to the 7th, and the 7th lord's placement, dignity, conjunctions, and strength. Explain marriage promise and spouse-related tendencies.

4. VENUS, JUPITER, AND EMOTIONAL COMPATIBILITY
   Review Venus for love, attraction, and marital harmony. Review Jupiter for wisdom, blessings, and as husband karaka in a woman's chart. Discuss each planet's dignity, affliction, conjunctions, aspects, and house placement.

5. FAMILY LIFE, DOMESTIC HAPPINESS, AND INTIMACY
   Study the 2nd house (family after marriage), 4th house (domestic peace), 8th house (in-laws, longevity, joint assets), 11th house (gains through spouse), and 12th house (intimacy, private life).

6. D9 NAVAMSHA MARRIAGE STRENGTH
   Analyze D9 lagna, D9 lagna lord, D9 7th house, D9 7th lord, Venus in D9, and D9 kendras (1st, 4th, 7th, 10th). State clearly whether D9 confirms, weakens, or improves D1 promise.

7. SPOUSE NATURE AND RELATIONSHIP STYLE
   Describe spouse tendencies from the 7th house sign, planets in the 7th, 7th lord's placement, Venus sign (D1 and D9), Jupiter's position, and Moon from the 7th house. Avoid harsh labels; use balanced, compassionate description.

8. DELAY, DENIAL, OR EARLY MARRIAGE TENDENCIES
   Check Saturn's influence on Venus, Moon, 7th house, or 7th lord. Assess D9 lagna and D9 7th affliction. Clearly distinguish: delay (Saturn/late dashas) vs difficulty (malefic affliction) vs true denial (only if multiple strong factors confirm in both D1 and D9). Also note early marriage patterns (strong 7th lord, Venus well-placed, benefic dashas active young).

9. LOVE MARRIAGE OR ARRANGED MARRIAGE INDICATORS
   Check: connections between 1st and 7th lords, 5th and 7th lords, Venus-Mars connection, 5th and 11th house involvement, Venus in lagna, Rahu influence, D9 support. Present as tendency, not certainty.

10. MARRIAGE CHALLENGES AND CONSCIOUS CORRECTIONS
     Identify sensitive patterns: affliction to 7th house/lord, Venus, D9 lagna, D9 7th/8th house, or strong malefic influences. Explain practical relationship lessons without fear. Suggest conscious corrections (communication, boundaries, counseling, emotional maturity).

11. MARRIAGE TIMING THROUGH DASHA AND TRANSIT
     Analyze marriage-supportive dashas: lagna lord, 7th lord, 2nd lord, Venus, Moon, Rahu, Jupiter, and planets connected to the 7th lord. Check double transit of Jupiter and Saturn on the 7th house, 7th lord, Venus, or D9 marriage factors. Give the most probable timing window as a range (month/year), with confidence level (High / Medium / Low).

12. MATCHMAKING REVIEW
     State clearly: "Partner chart not provided. Matchmaking analysis is not available for this reading."

13. PRACTICAL AND SPIRITUAL GUIDANCE
     End with relationship guidance: communication strategies, patience, realistic expectations, emotional maturity, family boundary management, professional counseling if needed.
     Suggest: strengthening Venus through kindness, cleanliness, respect, art, and gratitude; strengthening Jupiter through wisdom, ethics, guidance from elders, and dharmic living.
     For Saturn delay: recommend patience, responsibility, service, discipline, and avoiding rushed relationship decisions.

STYLE: Structured, compassionate, non-fatalistic, practical, and clear.
TONE: Respectful, calm, ethical, and empowering.
"""

def build_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    # --- Profile context (personal & birth details) ---
    ctx = structured_data.get("profile_context", {})
    name = ctx.get("name") or "Not provided"
    gender = ctx.get("gender") or "Not specified"
    birth_year = ctx.get("birth_year", "?")
    birth_month = ctx.get("birth_month", "?")
    birth_day = ctx.get("birth_day", "?")
    birth_hour = ctx.get("birth_hour", "?")
    birth_minute = ctx.get("birth_minute", "?")
    city = ctx.get("city", "?")
    country_code = ctx.get("country_code", "?")
    marriage_date = ctx.get("marriage_date")
    kids = ctx.get("kids")
    comments = ctx.get("comments")

    date_of_birth = (
        f"{birth_year}-{str(birth_month).zfill(2)}-{str(birth_day).zfill(2)}"
    )
    time_of_birth = f"{str(birth_hour).zfill(2)}:{str(birth_minute).zfill(2)}"
    place_of_birth = f"{city}, {country_code}"
    birth_time_note = (
        "Birth time fields are provided by the user. "
        "Assumed accurate unless stated otherwise."
    )

    # Derive marital status
    if marriage_date:
        marital_status = f"Married (marriage date on record: {marriage_date})"
    elif kids:
        marital_status = (
            f"Likely married or in committed relationship (has {kids} child/children)"
        )
    else:
        marital_status = "Unknown / Not specified"

    # Personal context block
    ctx_parts = []
    if marriage_date:
        ctx_parts.append(f"Marriage Date: {marriage_date}")
    if kids is not None:
        ctx_parts.append(f"Number of Children: {kids}")
    if comments:
        ctx_parts.append(f"Additional Notes: {comments}")
    personal_context = (
        "\n".join(ctx_parts) if ctx_parts else "No additional context provided."
    )

    # --- Lagna + sign order helper ---
    _sign_lords = {
        "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
        "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
        "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
    }

    planet_map = get_d1_planet_map(structured_data)
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")

    # --- D1 house lords (all 12) ---
    birth_planets = get_birth_planets(structured_data)
    bp_map = {p.get("planet"): p for p in birth_planets}

    # Build house → [planets] map for conjunction detection
    h_to_planets: dict = {}
    for p in birth_planets:
        h = p.get("house")
        if h:
            h_to_planets.setdefault(h, []).append(p.get("planet"))

    d1_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = bp_map.get(lord_name, {})
        lord_house = lord_data.get("house", "N/A")
        lord_sign = lord_data.get("sign", "N/A")
        lord_dignity = lord_data.get("dignity", "N/A")
        d1_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | Placed in House {lord_house} ({lord_sign})"
            f" | Dignity: {lord_dignity}"
        )
    d1_house_lords_str = "\n".join(d1_house_lord_lines)

    # --- Full D1 planetary data ---
    d1_lines = []
    for p in birth_planets:
        pname = p.get("planet", "")
        house = p.get("house")
        conditions = []
        if p.get("is_retrograde") == "Yes":
            conditions.append("Retrograde")
        if p.get("is_combust") == "Yes":
            conditions.append("Combust")
        cond_str = ", ".join(conditions) if conditions else "Direct/Normal"
        conjuncts = [
            x for x in h_to_planets.get(house, []) if x != pname
        ]
        conj_str = ", ".join(conjuncts) if conjuncts else "None"
        d1_lines.append(
            f"  {pname} → House: {house}"
            f" | Sign: {p.get('sign', 'N/A')}"
            f" | Degree: {p.get('degree', 'N/A')}°"
            f" | Nakshatra: {p.get('nakshatra', 'N/A')}"
            f" | Dignity: {p.get('dignity', 'N/A')}"
            f" | Conditions: {cond_str}"
            f" | Conjunct: {conj_str}"
        )
    d1_planets_str = "\n".join(d1_lines) if d1_lines else "Not available"

    # --- D9 data ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d9_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D9":
            d9_positions = chart.get("positions", [])
            break

    # D9 Lagna
    d9_asc = next(
        (p for p in d9_positions if p.get("planet") == "Ascendant"), {}
    )
    d9_lagna_sign = d9_asc.get("sign", "N/A")
    d9_lagna_lord = _sign_lords.get(d9_lagna_sign, "N/A")
    d9_lagna_str = f"{d9_lagna_sign} (Lord: {d9_lagna_lord})"

    # D9 house lords — derived from D9 ascendant
    d9_planet_map = {p.get("planet"): p for p in d9_positions}
    d9_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d9_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d9_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        # Calculate D9 house for this lord from its sign + D9 lagna
        try:
            d9_lagna_idx = _SIGN_ORDER.index(d9_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d9_house = ((lord_sign_idx - d9_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d9_house = "N/A"
        d9_house_lord_lines.append(
            f"  D9 House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D9 House {lord_d9_house} ({lord_sign})"
        )
    d9_house_lords_str = "\n".join(d9_house_lord_lines)

    # D9 planetary positions with calculated house numbers
    d9_planet_lines = []
    for p in d9_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d9_lagna_idx = _SIGN_ORDER.index(d9_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d9_house_num = ((p_sign_idx - d9_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d9_house_num = "N/A"
        d9_planet_lines.append(
            f"  {pname} → D9 House: {d9_house_num}"
            f" | Sign: {p_sign}"
            f" | Degree: {p.get('degree', 'N/A')}°"
        )
    d9_planets_str = (
        "\n".join(d9_planet_lines) if d9_planet_lines else "Not available"
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

    # --- Transits ---
    transit_raw = structured_data.get("transits", {})
    transits_list = transit_raw.get("data", {}).get("transits", [])
    transits_str = (
        json.dumps(transits_list, indent=2) if transits_list else "Not available"
    )

    return template.format(
        user_prompt=user_prompt,
        name=name,
        gender=gender,
        date_of_birth=date_of_birth,
        time_of_birth=time_of_birth,
        place_of_birth=place_of_birth,
        birth_time_note=birth_time_note,
        marital_status=marital_status,
        personal_context=personal_context,
        lagna=f"{lagna_sign} (Lord: {lagna_lord})",
        d1_house_lords=d1_house_lords_str,
        d1_planets=d1_planets_str,
        d9_lagna=d9_lagna_str,
        d9_house_lords=d9_house_lords_str,
        d9_planets=d9_planets_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
        transits=transits_str,
    )
