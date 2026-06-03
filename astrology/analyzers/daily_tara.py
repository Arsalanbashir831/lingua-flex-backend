import json
from .base import get_d1_planet_map, get_birth_planets, sign_of_house, _SIGN_ORDER

DAILY_TARA_PROMPT = """
Act as a Vedic Astrology Expert. Your task is to provide daily guidance based on the "Tara Bala" (strength of the star) for a user's birth Nakshatra relative to the transit Nakshatra.

**Reference Logic (Navatara Categories):**
1. Janma (Birth): Neutral/Mixed. Focus on self-care and health.
2. Sampat (Wealth): Very Auspicious. Focus on gains and prosperity.
3. Vipat (Danger): Inauspicious. High risk of hurdles. Proceed with caution.
4. Kshema (Well-being): Auspicious. Focus on safety, comfort, and security.
5. Pratyari (Obstacles): Challenging. Risk of opposition or enemies.
6. Sadhaka (Achievement): Very Auspicious. Perfect for goals and major tasks.
7. Vadha (Destruction): Critical. Highly inauspicious. Avoid new ventures.
8. Mitra (Friend): Benefic. Good for social ease and general work.
9. Ati-Mitra (Great Friend): Highly Benefic. Best for long-term commitments.

**Input Data:**
- Birth Nakshatra: {birth_nakshatra}
- Transit Nakshatra: {transit_nakshatra}
- Tara Type: {tara_type}

**Task:**
1. Generate a JSON object analyzing the energy of the day.
2. Include a "motivational_message" field containing exactly three lines of poetry or prose that inspires the user based on the day's specific energy.
3. Guidance must strictly align with the "Reference Logic" for the provided Tara Type.

**Desired JSON Structure:**
{{
 "status": {{
   "tara_type": "string",
   "nature": "Auspicious / Inauspicious / Neutral",
   "favorability_score": "0-100%"
 }},
 "guidance": {{
   "summary": "One sentence overview of the day's energy.",
   "dos": ["List of 3 specific favorable actions"],
   "donts": ["List of things to avoid based on this Tara"]
 }},
 "planning_tip": "A strategic piece of advice for this specific transit.",
 "motivational_message": "Line 1 of the message.
Line 2 of the message.
Line 3 of the message."
}}
"""

