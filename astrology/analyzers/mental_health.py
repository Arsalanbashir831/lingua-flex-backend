MENTAL_HEALTH_PROMPT = """
You are an expert Vedic Astrologer specializing in psychological and emotional analysis of birth charts.

Your task is to analyze a D1 (Birth) Chart to assess mental well-being, emotional stability, and psychological patterns using Vedic Astrology principles.

Focus specifically on:
- Moon as the Mind (emotional core)
- Mercury + Lagna as the cognitive filter (decision-making and processing)

-----------------------------------
INPUT DATA:
Lagna (Ascendant) Sign and Lord: {lagna}
Moon Position (Sign, House, Aspects/Conjunctions): {moon}
Mercury Position (Sign, House, Aspects/Conjunctions): {mercury}
4th House Condition (Sign, Lord, Planets, Aspects): {house4}
-----------------------------------

ANALYSIS FRAMEWORK:

1. MOON ANALYSIS (Emotional Core)
- Evaluate Moon's dignity (friendly, neutral, debilitated)
- Analyze conjunctions/aspects:

  If Moon + Mars -> check emotional reactivity, anger, impulsiveness
  If Moon + Rahu -> check anxiety, obsession, confusion
  If Moon + Saturn -> check depression, heaviness, emotional suppression
  If Moon + Ketu -> check detachment, dissociation, identity confusion

- Comment on emotional stability, sensitivity, and resilience

2. MERCURY + LAGNA ANALYSIS (Mental Filter)
- Evaluate Lagna and Lagna Lord strength (personality stability, grounding)
- Analyze Mercury strength:
  - Is Mercury strong or weak?
  - Does it stabilize emotions or amplify confusion?
- Determine whether the native can logically process emotions or gets overwhelmed

3. 4TH HOUSE ANALYSIS (Emotional Security)
- Assess emotional foundation, inner peace, and early nurturing
- Analyze:
  - 4th house condition
  - 4th lord strength
  - Moon's relationship with 4th house
- Identify possible issues related to:
  - lack of emotional security
  - maternal influence
  - unstable inner environment

4. SYNTHESIS
- Combine Moon + Mercury + Lagna + 4th house insights
- Clearly identify:
  - Core emotional pattern
  - Major psychological risks (if any)
  - Strengths in emotional resilience

5. REMEDY PLAN (MANDATORY OUTPUT)
Provide a structured holistic remedy plan:

A. Physical / Environment:
- Actions like decluttering, grounding activities, movement

B. Lifestyle:
- Diet suggestions (Sattvic where relevant)
- Hydration and daily routine improvements

C. Spiritual:
- Specific mantras (e.g., Om Namah Shivaya)
- Meditation or breathing practices

D. Cognitive:
- Guidance on acceptance (Svikarokti)
- Mental reframing strategies

{user_prompt}
-----------------------------------

OUTPUT FORMAT:
- Sectioned response (Moon Analysis, Mercury/Lagna, 4th House, Synthesis, Remedies)
- Clear, structured, and practical insights
- Avoid generic statements -- base conclusions on input data
"""

def build_prompt(template: str, structured_data: dict, user_prompt: str = "") -> str:
    """
    Extracts specific planet/house fields from the stored API data
    and injects them into the MENTAL_HEALTH_PROMPT named placeholders.

    Uses divisional_data (from the divisional-chart API) for D1 sign positions.
    birth_details_data contains house placements and dignity info.
    """
    # --- Parse D1 positions from divisional_data ---
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    d1_positions = []
    for chart in all_charts:
        if chart.get("chart") == "D1":
            d1_positions = chart.get("positions", [])
            break

    # Build a flat planet map from D1
    planet_map = {}
    for pos in d1_positions:
        planet_name = pos.get("planet", "")
        planet_map[planet_name] = {
            "sign": pos.get("sign", "N/A"),
            "degree": pos.get("degree", 0),
            "lord": pos.get("lord", "N/A"),
        }

    # --- Parse birth_details for house placements and dignity ---
    birth_raw = structured_data.get("birth_details", {})
    birth_planets = birth_raw.get("data", {}).get("planets", [])
    house_map = {}  # planet -> house number
    dignity_map = {}  # planet -> dignity
    nakshatra_map = {}  # planet -> nakshatra

    for p in birth_planets:
        name = p.get("planet", "")
        house_map[name] = p.get("house", "N/A")
        dignity_map[name] = p.get("dignity", "N/A")
        nakshatra_map[name] = p.get("nakshatra", "N/A")

    # --- Build Lagna string ---
    asc = planet_map.get("Ascendant", {})
    lagna_sign = asc.get("sign", "N/A")
    lagna_lord = asc.get("lord", "N/A")
    lagna_str = f"{lagna_sign} (Lord: {lagna_lord})"

    # --- Build Moon string ---
    moon_d1 = planet_map.get("Moon", {})
    moon_house = house_map.get("Moon", "N/A")
    # Find planets conjunct Moon (same house)
    moon_conjuncts = [
        name
        for name, h in house_map.items()
        if h == moon_house and name != "Moon" and name != "Ascendant"
    ]
    moon_str = (
        f"Sign: {moon_d1.get('sign', 'N/A')}, "
        f"House: {moon_house}, "
        f"Nakshatra: {nakshatra_map.get('Moon', 'N/A')}, "
        f"Dignity: {dignity_map.get('Moon', 'N/A')}, "
        f"Conjunct: {moon_conjuncts if moon_conjuncts else 'None'}"
    )

    # --- Build Mercury string ---
    mercury_d1 = planet_map.get("Mercury", {})
    mercury_house = house_map.get("Mercury", "N/A")
    mercury_conjuncts = [
        name
        for name, h in house_map.items()
        if h == mercury_house and name != "Mercury" and name != "Ascendant"
    ]
    mercury_str = (
        f"Sign: {mercury_d1.get('sign', 'N/A')}, "
        f"House: {mercury_house}, "
        f"Nakshatra: {nakshatra_map.get('Mercury', 'N/A')}, "
        f"Dignity: {dignity_map.get('Mercury', 'N/A')}, "
        f"Conjunct: {mercury_conjuncts if mercury_conjuncts else 'None'}"
    )

    # --- Build 4th House string ---
    house4_sign = "N/A"
    house4_lord = "N/A"
    for p in birth_planets:
        if p.get("house") == 4:
            house4_sign = p.get("rashi", "N/A")
            house4_lord = p.get("house_lord", "N/A")
            break

    house4_planets = [
        name for name, h in house_map.items() if h == 4 and name != "Ascendant"
    ]
    house4_str = (
        f"Sign: {house4_sign}, "
        f"Lord: {house4_lord}, "
        f"Planets in 4th: {house4_planets if house4_planets else 'None'}"
    )

    return template.format(
        user_prompt=user_prompt,
        lagna=lagna_str,
        moon=moon_str,
        mercury=mercury_str,
        house4=house4_str,
    )
