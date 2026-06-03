import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D2_HORA_PROMPT = """
You are an ethical Vedic astrology analyst specializing in D2 Hora chart interpretation. Analyze the D2 chart using the provided planetary details to understand wealth patterns, earning capacity, savings, family resources, financial habits, speech, values, food habits, and practical guidance for financial stability.

ETHICAL GUIDELINES:
- Do not make fatalistic or fear-based predictions about wealth, poverty, debt, bankruptcy, inheritance, or financial destiny.
- Do not guarantee financial success, loss, promotion, business profit, investment return, or wealth accumulation.
- Present interpretations as tendencies, strengths, challenges, and areas for conscious action.
- For investments, taxes, debt, legal matters, or financial planning, advise consulting qualified professionals.
- Use practical, respectful, and empowering language.
- Avoid superstition, fear-based remedies, or expensive ritual dependency.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}

HORA CALCULATION METHOD:
{hora_method_note}
-----------------------------------

D2 HORA CHART DATA:

D2 Lagna (Ascendant): {d2_lagna}

D2 House Lords (House Sign Lord Where Lord Sits in D2):
{d2_house_lords}

D2 Planetary Placements (with Hora Type):
{d2_planets}

Sun Hora vs Moon Hora Balance:
{hora_balance}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE:
{d1_cross_ref}

-----------------------------------
VIMSHOTTARI DASHA (for timing financial themes):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D2 CORE INDICATORS (Evaluate Each):
- D2 Lagna: Overall financial orientation, wealth identity, relationship with resources
- D2 Lagna Lord: How the native pursues, manages, preserves, or spends wealth
- Sun Hora: Self-earned wealth, authority, leadership, confidence, government, status, independence, visible achievement
- Moon Hora: Family support, liquidity, nourishment, public connection, adaptability, trade, food, hospitality, flow of resources
- Jupiter in D2: Wealth wisdom, expansion, blessings, ethics, savings, financial protection, long-term prosperity
- Venus in D2: Comforts, luxuries, vehicles, enjoyment, beauty, value creation, material refinement
- Mercury in D2: Trade, business, calculation, accounting, communication, finance, commercial intelligence
- Saturn in D2: Savings discipline, delay, long-term planning, responsibility, austerity, wealth through patience
- Mars in D2: Risk-taking, land, technical work, entrepreneurship, competition, active wealth-building
- Rahu in D2: Amplified financial ambition, unconventional income, foreign links, speculation, financial confusion if unmanaged
- Ketu in D2: Detachment from wealth, past-life familiarity with resources, unconventional financial behavior

D2 HOUSE MEANINGS:
House 1: Overall wealth karma, financial identity, approach to money, confidence in handling resources
House 2: Savings, family wealth, speech, food, stored resources, values, financial security
House 3: Self-effort in earning, courage in financial decisions, communication-based income, sales, writing, enterprise
House 4: Assets, property comfort, family support, emotional security through wealth, vehicles, stable resources
House 5: Speculation, intelligence, investment judgment, past-life merit, creativity, wealth through learning or advisory skills
House 6: Debts, loans, financial disputes, service income, competition, daily work, discipline for financial stability
House 7: Business partnerships, clients, contracts, trade, marketplace income, financial dealings with others
House 8: Inheritance, sudden gains or losses, taxes, insurance, hidden money, joint assets, financial transformation
House 9: Fortune, blessings, dharmic wealth, father or guru support, ethical earning, higher financial wisdom
House 10: Career-based income, professional status, authority, public work, wealth through responsibility
House 11: Gains, profits, networks, fulfillment of financial desires, elder support, income expansion
House 12: Expenses, charity, losses, luxury spending, foreign expenses, spiritual giving, money used for comfort or escape

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 12 sections in order:

1. BIRTH TIME AND D2 RELIABILITY
   Assess birth time accuracy and its effect on D2 interpretation. State that divisional charts require accurate birth time.

2. HORA METHOD USED
   State the Hora method used. Note that different methods (Parashari, Jagannatha, etc.) may give different D2 placements.

3. OVERALL D2 LAGNA INTERPRETATION
   Interpret the D2 ascendant sign, lagna lord, planets in the 1st house, and aspects to the lagna. Explain the native's general financial nature and approach to resources.

4. SUN HORA AND MOON HORA BALANCE
   State how many planets are in Sun Hora vs Moon Hora. Explain whether wealth is more self-driven/authority-based or family-supported/public-facing/adaptive or mixed.

5. KEY WEALTH PLANETS
   Analyze Jupiter, Venus, Mercury, Saturn, and the D2 2nd and 11th lords in detail. Explain wealth wisdom, comfort, trade intelligence, saving discipline, and gain potential.

6. HOUSE-BY-HOUSE D2 INTERPRETATION
   Analyze all 12 D2 houses using the house meanings above. For each house, evaluate: sign, lord placement, planets present, benefic or malefic influence, and practical wealth meaning.

7. EARNING CAPACITY AND INCOME PATTERNS
   Study the D2 2nd, 6th, 10th, and 11th houses. Describe earning capacity, career income, service income, and financial consistency. Cross-reference with D1 wealth indicators.

8. SAVINGS, FAMILY RESOURCES, AND VALUES
   Study the D2 2nd and 4th houses, Moon, and benefic influences. Explain family support, savings habits, food and lifestyle values, speech, and emotional security through money.

9. RISKS, EXPENSES, AND FINANCIAL CAUTIONS
   Study the D2 5th, 8th, 12th houses and any Rahu, Mars, or afflicted Mercury/Jupiter. Discuss speculation tendencies, sudden changes, impulsive spending, or hidden liabilities using careful, non-fear-based language.

10. D1-D2 REPEATED THEMES
     Confirm whether wealth themes from D1 (2nd lord, 11th lord, Jupiter, Venus, Mercury condition) are repeated, supported, or contradicted in D2. State overall wealth promise consistency.

11. DASHA-BASED FINANCIAL THEMES
     Explain how the current Mahadasha and Antardasha lords operate in D1 and D2. Describe financial themes, opportunities, and cautions active during this period - not guaranteed events.

12. PRACTICAL FINANCIAL AND SPIRITUAL GUIDANCE
     Summarize financial strengths and wealth-building style. Suggest disciplined saving, budgeting, ethical earning, avoiding impulsive decisions, generosity within capacity, and consulting professionals for debt, tax, investment, or legal matters. Encourage financial literacy and long-term planning.

STYLE: Structured, practical, compassionate, non-fatalistic, and clear.
TONE: Calm, ethical, empowering, and grounded.
"""

def build_d2_hora_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    _sign_lords = {
        "Ari": "Mars", "Tau": "Venus", "Gem": "Mercury", "Can": "Moon",
        "Leo": "Sun", "Vir": "Mercury", "Lib": "Venus", "Sco": "Mars",
        "Sag": "Jupiter", "Cap": "Saturn", "Aqu": "Saturn", "Pis": "Jupiter",
    }

    def hora_type(sign: str) -> str:
        if sign == "Leo":
            return "Sun Hora"
        elif sign in ("Can", "Cancer"):
            return "Moon Hora"
        else:
            return f"Extended ({sign})"

    birth_time_note = (
        "Birth time provided by user. D2 divisional charts require accurate birth "
        "time — if birth time is approximate or unknown, D2 positions may shift."
    )
    hora_method_note = (
        "Parashari Hora (traditional): planets fall in Leo (Sun Hora) for "
        "self-earned wealth / authority, or Cancer (Moon Hora) for family support / "
        "liquidity / public income. If your software uses an extended Hora method "
        "(Jagannatha etc.), planet signs will differ."
    )

    # --- Extract D2 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d2_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D2":
            d2_positions = chart.get("positions", [])
            break

    # D2 Lagna
    d2_asc = next(
        (p for p in d2_positions if p.get("planet") == "Ascendant"), {}
    )
    d2_lagna_sign = d2_asc.get("sign", "N/A")
    d2_lagna_lord = _sign_lords.get(d2_lagna_sign, "N/A")
    d2_lagna_str = (
        f"{d2_lagna_sign} (Lord: {d2_lagna_lord})"
        f" | {hora_type(d2_lagna_sign)}"
    )

    # D2 house lords (all 12) — derived from D2 ascendant
    d2_planet_map = {p.get("planet"): p for p in d2_positions}
    d2_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d2_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d2_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d2_lagna_idx = _SIGN_ORDER.index(d2_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d2_house = ((lord_sign_idx - d2_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d2_house = "N/A"
        d2_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D2 House {lord_d2_house} ({lord_sign})"
            f" | {hora_type(lord_sign)}"
        )
    d2_house_lords_str = "\n".join(d2_house_lord_lines)

    # D2 planetary placements with hora type
    sun_hora_count = 0
    moon_hora_count = 0
    other_hora_count = 0
    d2_planet_lines = []
    for p in d2_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        p_hora = hora_type(p_sign)
        # house in D2
        try:
            d2_lagna_idx = _SIGN_ORDER.index(d2_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d2_house_num = ((p_sign_idx - d2_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d2_house_num = "N/A"
        d2_planet_lines.append(
            f"  {pname} → D2 House: {d2_house_num}"
            f" | Sign: {p_sign}"
            f" | Degree: {p.get('degree', 'N/A')}°"
            f" | Hora: {p_hora}"
        )
        if p_hora == "Sun Hora":
            sun_hora_count += 1
        elif p_hora == "Moon Hora":
            moon_hora_count += 1
        else:
            other_hora_count += 1

    d2_planets_str = "\n".join(d2_planet_lines) if d2_planet_lines else "Not available"

    # Hora balance summary
    hora_balance_str = (
        f"  Sun Hora planets: {sun_hora_count} (self-earned wealth, authority, independence)\n"
        f"  Moon Hora planets: {moon_hora_count} (family support, liquidity, public income)\n"
    )
    if other_hora_count:
        hora_balance_str += (
            f"  Extended Hora (non-Leo/Cancer): {other_hora_count} planets "
            f"(Jagannatha or alternate D2 method in use)\n"
        )
    if sun_hora_count > moon_hora_count:
        hora_balance_str += "  Dominant theme: Self-driven / authority-based wealth"
    elif moon_hora_count > sun_hora_count:
        hora_balance_str += "  Dominant theme: Family-supported / liquid / public-facing wealth"
    else:
        hora_balance_str += "  Balance: Mixed self-earned and family/public wealth"

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    planet_map = get_d1_planet_map(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")

    bp_map = {p.get("planet"): p for p in birth_planets}

    def _d1_lord_of_house(h: int) -> str:
        h_sign = sign_of_house(d1_lagna_sign, h)
        return _sign_lords.get(h_sign, "N/A")

    d1_2nd_lord = _d1_lord_of_house(2)
    d1_11th_lord = _d1_lord_of_house(11)

    def _planet_summary(planet_name: str) -> str:
        p = bp_map.get(planet_name, {})
        return (
            f"House {p.get('house', 'N/A')}"
            f" | Sign: {p.get('sign', 'N/A')}"
            f" | Dignity: {p.get('dignity', 'N/A')}"
        )

    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 2nd Lord: {d1_2nd_lord} — {_planet_summary(d1_2nd_lord)}\n"
        f"  D1 11th Lord: {d1_11th_lord} — {_planet_summary(d1_11th_lord)}\n"
        f"  D1 Jupiter — {_planet_summary('Jupiter')}\n"
        f"  D1 Venus  — {_planet_summary('Venus')}\n"
        f"  D1 Mercury — {_planet_summary('Mercury')}"
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
        hora_method_note=hora_method_note,
        d2_lagna=d2_lagna_str,
        d2_house_lords=d2_house_lords_str,
        d2_planets=d2_planets_str,
        hora_balance=hora_balance_str,
        d1_cross_ref=d1_cross_ref_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
