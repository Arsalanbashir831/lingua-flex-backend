from .mental_health import MENTAL_HEALTH_PROMPT, build_prompt as build_mental_health_prompt
from .btr import KP_BTR_PROMPT, build_prompt as build_btr_prompt
from .marriage import MARRIAGE_TIMING_PROMPT, build_prompt as build_marriage_prompt

from .d2_hora import D2_HORA_PROMPT, build_d2_hora_prompt
from .d4_chaturthamsha import D4_CHATURTHAMSHA_PROMPT, build_d4_chaturthamsha_prompt
from .d7_saptamsha import D7_SAPTAMSHA_PROMPT, build_d7_saptamsha_prompt
from .d10_dashamsha import D10_DASHAMSHA_PROMPT, build_d10_dashamsha_prompt
from .d12_dwadashamsha import D12_DWADASHAMSHA_PROMPT, build_d12_dwadashamsha_prompt
from .d60_shashtiamsha import D60_SHASHTIAMSHA_PROMPT, build_d60_shashtiamsha_prompt
from .d27_saptavimshamsha import D27_SAPTAVIMSHAMSHA_PROMPT, build_d27_saptavimshamsha_prompt

from .benefic_planets import BENEFIC_PLANETS_PROMPT, build_benefic_planets_prompt
from .malefic_planets import MALEFIC_PLANETS_PROMPT, build_malefic_planets_prompt
from .chart_analysis import CHART_ANALYSIS_PROMPT, build_chart_analysis_prompt
from .planetary_states import PLANETARY_STATES_PROMPT, build_planetary_states_prompt
from .lagna_lord import LAGNA_LORD_PROMPT, build_lagna_lord_prompt
from .rashi_planets import RASHI_PLANETS_PROMPT, build_rashi_planets_prompt
from .challenges import CHALLENGES_PROMPT, build_challenges_prompt
from .astro_energy import ASTRO_ENERGY_PROMPT, build_astro_energy_prompt

from .prosperity_sav import MASTER_SAV_PROMPT, build_sav_prompt
from .parasari import PARASARI_PROMPT, build_parasari_prompt
from .navatara import NAVATARA_PROMPT, build_navatara_prompt
from .medical import MEDICAL_PROMPT, build_medical_prompt
from .darakaraka import DARAKARAKA_PROMPT, build_darakaraka_prompt
from .daily_tara import DAILY_TARA_PROMPT
from .foreign_travel import FOREIGN_TRAVEL_PROMPT, build_foreign_travel_prompt

__all__ = [
    "MENTAL_HEALTH_PROMPT", "build_mental_health_prompt",
    "KP_BTR_PROMPT", "build_btr_prompt",
    "MARRIAGE_TIMING_PROMPT", "build_marriage_prompt",
    "D2_HORA_PROMPT", "build_d2_hora_prompt",
    "D4_CHATURTHAMSHA_PROMPT", "build_d4_chaturthamsha_prompt",
    "D7_SAPTAMSHA_PROMPT", "build_d7_saptamsha_prompt",
    "D10_DASHAMSHA_PROMPT", "build_d10_dashamsha_prompt",
    "D12_DWADASHAMSHA_PROMPT", "build_d12_dwadashamsha_prompt",
    "D60_SHASHTIAMSHA_PROMPT", "build_d60_shashtiamsha_prompt",
    "D27_SAPTAVIMSHAMSHA_PROMPT", "build_d27_saptavimshamsha_prompt",
    "BENEFIC_PLANETS_PROMPT", "build_benefic_planets_prompt",
    "MALEFIC_PLANETS_PROMPT", "build_malefic_planets_prompt",
    "CHART_ANALYSIS_PROMPT", "build_chart_analysis_prompt",
    "PLANETARY_STATES_PROMPT", "build_planetary_states_prompt",
    "ASTRO_ENERGY_PROMPT", "build_astro_energy_prompt",
    "RASHI_PLANETS_PROMPT", "build_rashi_planets_prompt",
    "LAGNA_LORD_PROMPT", "build_lagna_lord_prompt",
    "CHALLENGES_PROMPT", "build_challenges_prompt",
    "MASTER_SAV_PROMPT", "build_sav_prompt",
    "PARASARI_PROMPT", "build_parasari_prompt",
    "NAVATARA_PROMPT", "build_navatara_prompt",
    "MEDICAL_PROMPT", "build_medical_prompt",
    "DARAKARAKA_PROMPT", "build_darakaraka_prompt",
    "DAILY_TARA_PROMPT",
    "FOREIGN_TRAVEL_PROMPT", "build_foreign_travel_prompt",
]
