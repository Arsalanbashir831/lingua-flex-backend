_SIGN_ORDER = [
    "Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis",
]

def sign_of_house(lagna_sign: str, house_offset: int) -> str:
    """Returns sign that falls in (lagna + house_offset - 1) position."""
    try:
        idx = _SIGN_ORDER.index(lagna_sign)
        return _SIGN_ORDER[(idx + house_offset - 1) % 12]
    except ValueError:
        return "N/A"

def get_d1_planet_map(structured_data: dict) -> dict:
    """Returns {planet_name: {sign, degree, lord}} from divisional_data D1."""
    divisional_raw = structured_data.get("divisional_data", {})
    all_charts = divisional_raw.get("data", {}).get("charts", [])
    for chart in all_charts:
        if chart.get("chart") == "D1":
            return {p["planet"]: p for p in chart.get("positions", [])}
    return {}

def get_birth_planets(structured_data: dict) -> list:
    """Returns planet list from birth_details with house, rashi, dignity."""
    return (
        structured_data.get("birth_details", {}).get("data", {}).get("planets", [])
    )
