import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

D4_CHATURTHAMSHA_PROMPT = """
You are an ethical Vedic astrology analyst specializing in D4 Chaturthamsha chart interpretation. Analyze the D4 chart using the provided planetary details to understand property, assets, home, residence, vehicles, comforts, material stability, emotional peace, inner happiness, and the native's relationship with security and resources.

ETHICAL GUIDELINES:
- Do not make fatalistic or fear-based predictions about property loss, wealth, disputes, inheritance, or family matters.
- Do not guarantee property purchase, real estate gains, legal victory, wealth accumulation, or permanent happiness.
- Present interpretations as tendencies, strengths, challenges, and areas for conscious action.
- For property, legal, tax, investment, or financial decisions, advise consulting qualified professionals.
- Use compassionate and practical language.
- If birth time accuracy is uncertain, clearly state that D4 interpretation may change because divisional charts are sensitive to birth-time errors.
- Avoid superstition, fear-based remedies, or expensive ritual dependency.

-----------------------------------
BIRTH TIME NOTE:
{birth_time_note}
-----------------------------------

D4 CHATURTHAMSHA CHART DATA:

D4 Lagna (Ascendant): {d4_lagna}

D4 House Lords (House Sign Lord Where Lord Sits in D4):
{d4_house_lords}

D4 Planetary Placements (with Sign, House, Dignity, and D4 Division):
{d4_planets}

D4 Divisions Summary (Sanaki, Sanand, Sanat_Kumar, Sanatan):
{d4_divisions_summary}

-----------------------------------
D1 BIRTH CHART CROSS-REFERENCE:
{d1_cross_ref}

-----------------------------------
VIMSHOTTARI DASHA (for timing property and stability themes):
Current Mahadasha: {mahadasha}
Current Antardasha: {antardasha}

Upcoming Antardasha Sequence:
{dasha_sequence}
-----------------------------------

D4 CORE INDICATORS (Evaluate Each):
- D4 Lagna: Overall relationship with property, assets, comfort, emotional security, and happiness.
- D4 Lagna Lord: How the native pursues stability, property, and peace.
- D4 4th House: Real happiness, home, residence, inner contentment, mother, land, vehicles, and emotional peace.
- D4 4th Lord: Main controller of property comfort, residence, and inner stability.
- Moon: Natural significator of emotional peace, comfort, mother, and inner satisfaction.
- Mars: Land, buildings, property activity, construction, disputes, and risk-taking in real estate matters.
- Venus: Comforts, luxury, vehicles, beauty of home, pleasure, and material enjoyment.
- Saturn: Long-term property, delay, responsibility, old property, land, structure, and patience.
- Jupiter: Blessings, expansion, protection, family support, ethical use of wealth, and stable growth.

D4 DIVISIONS:
- Sanaki (0°00′ to 7°30′): Strong pursuit of happiness, desire for comfort, restlessness, and active effort to acquire property or security.
- Sanand (7°30′ to 15°00′): Happiness with acceptance, inner contentment, emotional steadiness, and ability to enjoy what is available.
- Sanat_Kumar (15°00′ to 22°30′): Youthful, changing, adaptive happiness; finding comfort through new experiences and changing life stages.
- Sanatan (22°30′ to 30°00′): Stable, eternal, mature happiness; inner peace that is less dependent on outer circumstances.

D4 HOUSE MEANINGS:
House 1: Overall property karma, wealth usage, assets, comfort-seeking nature, and how the native uses resources for happiness or stress.
House 2: Family values around wealth, family asset usage, and whether resources are used wisely or carelessly.
House 3: Change of residence, courage to invest, risk-taking in property matters, movement, relocation, and effort toward acquiring assets.
House 4: Home, land, vehicles, mother, inner peace, real happiness, satisfaction, residence, and emotional security.
House 5: Long-lasting assets, past-life merit connected with property, intelligent investment, blessings through accumulated merits.
House 6: Property disputes, loans, debts, legal issues, division among siblings, conflicts over assets, and practical obstacles.
House 7: Public perception of wealth, how society sees the native's comfort or status, property projection, and dealings with others.
House 8: Sudden changes in property, inheritance, hidden property matters, transformation of mindset, and instability or breakthroughs.
House 9: Use of wealth for dharma, pilgrimage, charity, ethical blessings, and fortune through property.
House 10: Actions affecting property and happiness; whether the native increases or damages assets through personal choices.
House 11: Gains from property, fulfillment of asset-related desires, income through real estate, networks, and support.
House 12: Expenses on property, luxury, desires, travel, charity, spiritual expenditure, losses, or investment-related outflow.

{user_prompt}
-----------------------------------

OUTPUT FORMAT - Provide ALL 11 sections in order:

1. BIRTH TIME AND D4 RELIABILITY
   Assess birth time accuracy and its effect on D4 interpretation. State that divisional charts require accurate birth time.

2. OVERALL D4 LAGNA INTERPRETATION
   Interpret the D4 ascendant sign, lagna lord, planets in the 1st house, and aspects to the lagna. Explain the native's overall relationship with property, comfort, assets, and happiness.

3. 4TH HOUSE, 4TH LORD, AND INNER HAPPINESS
   Give special importance to the D4 4th house, 4th lord, planets placed there, aspects, dignity, and benefic or challenging influences. Explain home, land, vehicles, mother, peace, satisfaction, and emotional security.

4. MOON AND EMOTIONAL COMFORT
   Review the Moon as the natural significator of comfort, peace, mother, and emotional happiness. Interpret its sign, house, dignity, conjunctions, and aspects in D4.

5. PROPERTY, ASSETS, AND WEALTH USAGE
   Study the 1st, 2nd, 10th, 11th, and 12th houses to explain how the native earns, uses, increases, spends, or loses resources connected with property and comfort.

6. RESIDENCE, MOVEMENT, AND HOME STABILITY
   Study the 3rd house and its lord for change of residence, relocation, property movement, rental shifts, or practical efforts toward acquiring assets.

7. DISPUTES, LOANS, RISKS, AND CAUTIONS
   Handle the 6th, 8th, and 12th houses carefully. Discuss loans, disputes, sudden changes, inheritance, hidden issues, expenses, or property stress without making fear-based predictions.

8. BLESSINGS, GAINS, AND LONG-TERM ASSETS
   Study the 5th, 9th, and 11th houses for past-life merit, blessings, property fortune, dharmic use of wealth, and gains through assets.

9. D1-D4 REPEATED THEMES
   Compare D4 themes with the D1 4th house, 4th lord, Moon, Mars, Venus. Confirm whether property and happiness themes repeat across D1 and D4.

10. DASHA-BASED PROPERTY THEMES
     Explain how the current Mahadasha and Antardasha lords operate in D4. Describe possible property, residence, comfort, or emotional themes without giving fixed predictions.

11. PRACTICAL, FINANCIAL, AND SPIRITUAL GUIDANCE
     Summarize property potential, asset management style, emotional comfort, residence themes, risks, blessings, and practical guidance for stability and peace. Suggest practical planning, documentation, financial discipline, respectful familial behavior, and professional consultation.

STYLE: Structured, practical, compassionate, non-fatalistic, and clear.
TONE: Calm, ethical, empowering, and grounded.
"""

def build_d4_chaturthamsha_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
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

    def get_d4_division(deg_str_or_num) -> str:
        d = parse_degree(deg_str_or_num)
        d = d % 30.0
        if d < 7.5:
            return "Sanaki (0°00′ to 7°30′: Active effort, pursuit of happiness)"
        elif d < 15.0:
            return "Sanand (7°30′ to 15°00′: Acceptance, inner contentment)"
        elif d < 22.5:
            return "Sanat_Kumar (15°00′ to 22°30′: Youthful, adaptive happiness)"
        else:
            return "Sanatan (22°30′ to 30°00′: Stable, eternal, mature happiness)"

    birth_time_note = (
        "Birth time provided by user. D4 divisional charts require accurate birth "
        "time — if birth time is approximate or unknown, D4 positions may shift."
    )

    # --- Extract D4 positions ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d4_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D4":
            d4_positions = chart.get("positions", [])
            break

    planet_map = get_d1_planet_map(structured_data)

    # D4 Lagna
    d4_asc = next(
        (p for p in d4_positions if p.get("planet") == "Ascendant"), {}
    )
    d4_lagna_sign = d4_asc.get("sign", "N/A")
    d4_lagna_lord = _sign_lords.get(d4_lagna_sign, "N/A")
    
    # Lagna division based on D1 Ascendant degree
    d1_asc = planet_map.get("Ascendant", {})
    d1_asc_deg = d1_asc.get("degree", 0.0)
    d4_lagna_division = get_d4_division(d1_asc_deg)
    d4_lagna_str = f"{d4_lagna_sign} (Lord: {d4_lagna_lord}) | Division: {d4_lagna_division}"

    # D4 house lords (all 12)
    d4_planet_map = {p.get("planet"): p for p in d4_positions}
    d4_house_lord_lines = []
    for h in range(1, 13):
        h_sign = sign_of_house(d4_lagna_sign, h)
        lord_name = _sign_lords.get(h_sign, "N/A")
        lord_data = d4_planet_map.get(lord_name, {})
        lord_sign = lord_data.get("sign", "N/A")
        try:
            d4_lagna_idx = _SIGN_ORDER.index(d4_lagna_sign)
            lord_sign_idx = _SIGN_ORDER.index(lord_sign)
            lord_d4_house = ((lord_sign_idx - d4_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            lord_d4_house = "N/A"
        
        # Get lord D1 degree to calculate its division
        lord_d1_data = planet_map.get(lord_name, {})
        lord_d1_deg = lord_d1_data.get("degree", 0.0)
        lord_division = get_d4_division(lord_d1_deg)
        
        d4_house_lord_lines.append(
            f"  House {h} ({h_sign}) → Lord: {lord_name}"
            f" | In D4 House {lord_d4_house} ({lord_sign})"
            f" | Division: {lord_division}"
        )
    d4_house_lords_str = "\n".join(d4_house_lord_lines)

    # D4 planetary placements
    d4_planet_lines = []
    divisions_count = {"Sanaki": 0, "Sanand": 0, "Sanat_Kumar": 0, "Sanatan": 0}
    for p in d4_positions:
        pname = p.get("planet", "")
        if pname == "Ascendant":
            continue
        p_sign = p.get("sign", "N/A")
        try:
            d4_lagna_idx = _SIGN_ORDER.index(d4_lagna_sign)
            p_sign_idx = _SIGN_ORDER.index(p_sign)
            d4_house_num = ((p_sign_idx - d4_lagna_idx) % 12) + 1
        except (ValueError, AttributeError):
            d4_house_num = "N/A"
        
        p_dignity = p.get("dignity", "N/A")
        
        # Division based on D1 degree
        p_d1_data = planet_map.get(pname, {})
        p_d1_deg = p_d1_data.get("degree", 0.0)
        p_division = get_d4_division(p_d1_deg)
        
        div_key = p_division.split(" (")[0]
        if div_key in divisions_count:
            divisions_count[div_key] += 1
            
        d4_planet_lines.append(
            f"  {pname} → D4 House: {d4_house_num}"
            f" | Sign: {p_sign}"
            f" | D4 Degree: {p.get('degree', 'N/A')}°"
            f" | Dignity: {p_dignity}"
            f" | D4 Division: {p_division}"
        )
    d4_planets_str = "\n".join(d4_planet_lines) if d4_planet_lines else "Not available"

    # D4 divisions summary
    d4_divisions_summary_str = (
        f"  Sanaki planets: {divisions_count['Sanaki']} (desire for comfort, active effort)\n"
        f"  Sanand planets: {divisions_count['Sanand']} (inner contentment, emotional steadiness)\n"
        f"  Sanat_Kumar planets: {divisions_count['Sanat_Kumar']} (adaptive happiness, changing life stages)\n"
        f"  Sanatan planets: {divisions_count['Sanatan']} (eternal / mature happiness, stable inner peace)\n"
    )

    # --- D1 cross-reference ---
    birth_planets = get_birth_planets(structured_data)
    d1_asc = planet_map.get("Ascendant", {})
    d1_lagna_sign = d1_asc.get("sign", "N/A")
    d1_lagna_lord = d1_asc.get("lord", "N/A")
    bp_map = {p.get("planet"): p for p in birth_planets}

    d1_4th_lord = _d1_lord_of_house(4)

    def _planet_summary(planet_name: str) -> str:
        p = bp_map.get(planet_name, {})
        return (
            f"House {p.get('house', 'N/A')}"
            f" | Sign: {p.get('sign', 'N/A')}"
            f" | Dignity: {p.get('dignity', 'N/A')}"
        )

    d1_cross_ref_str = (
        f"  D1 Lagna: {d1_lagna_sign} (Lord: {d1_lagna_lord})\n"
        f"  D1 4th House Lord: {d1_4th_lord} — {_planet_summary(d1_4th_lord)}\n"
        f"  D1 Moon — {_planet_summary('Moon')}\n"
        f"  D1 Mars (Significator of Land/Property) — {_planet_summary('Mars')}\n"
        f"  D1 Venus (Significator of Vehicles/Comforts) — {_planet_summary('Venus')}"
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
        d4_lagna=d4_lagna_str,
        d4_house_lords=d4_house_lords_str,
        d4_planets=d4_planets_str,
        d4_divisions_summary=d4_divisions_summary_str,
        d1_cross_ref=d1_cross_ref_str,
        mahadasha=mahadasha_str,
        antardasha=antardasha_str,
        dasha_sequence=dasha_sequence_str,
    )
