"""
astrology/report_generator.py
——————————————————————————————
Generates an Astrology Report PDF and uploads it to Supabase Storage.

Phase 1 (NOW):
  Produces a multi-page dummy PDF using ReportLab with realistic-looking
  astrology placeholder sections.  The first ~30% of sections become the
  free preview_content returned to unauthenticated / unpaid callers.

Phase 2 (LATER):
  Replace _build_full_report() with a call to the real Astro Report API.
  The public surface (generate_report / upload_report_to_supabase) stays
  identical — views and services never need to change.
"""

import io
import uuid
import logging
import textwrap
from datetime import datetime
from typing import Tuple

from django.conf import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Section content (Phase 1 dummy data)
# ──────────────────────────────────────────────────────────────────────────────

_DUMMY_SECTIONS = [
    {
        "title": "Executive Summary",
        "body": (
            "Your Vedic birth chart reveals a soul on a powerful journey of self-discovery "
            "and growth. With your Ascendant (Lagna) setting the tone of your personality and "
            "life path, the planets in your chart form a unique cosmic blueprint that guides "
            "your strengths, challenges, and destiny. This report provides a comprehensive "
            "analysis of your natal chart, transit influences, divisional charts (Vargas), "
            "Vimshottari Dasha timeline, and key life-area predictions."
        ),
    },
    {
        "title": "Lagna (Ascendant) & Rising Sign Analysis",
        "body": (
            "The Lagna lord — the planet ruling your ascendant sign — plays a pivotal role in "
            "shaping your outward personality and life direction. Its placement by house and "
            "sign colours every area of your life. Planets aspecting or conjoining the Lagna "
            "lord further modify your self-expression, health, and approach to the world.\n\n"
            "Your first house indicates vitality, physical appearance, and the overall tone of "
            "your personality. Pay close attention to planets occupying the first house or "
            "casting strong aspects onto it."
        ),
    },
    {
        "title": "Planetary Positions & Strengths",
        "body": (
            "Each of the nine Vedic planets (Navagrahas) occupies a specific sign and house in "
            "your chart. Their relative strengths are calculated through:\n"
            "  • Shadbala (six-fold strength)\n"
            "  • Ashtakavarga (eight-fold divisional points)\n"
            "  • Vargottama placement (same sign in D1 and D9)\n\n"
            "Strong planets act as benefactors in their signified life areas; weak or afflicted "
            "planets indicate areas where conscious effort and remedial measures are recommended."
        ),
    },
    {
        "title": "Nakshatra Analysis & Moon Sign",
        "body": (
            "Your Moon's nakshatra (lunar mansion) at the time of birth is one of the most "
            "important factors in Vedic astrology. It determines your Vimshottari Dasha "
            "starting balance, your emotional temperament, and your instinctive responses to "
            "life situations.\n\n"
            "The 27 nakshatras are grouped into three categories — Deva (divine), Manushya "
            "(human), and Rakshasa (demonic) — each carrying distinct psychological and "
            "spiritual characteristics."
        ),
    },
    {
        "title": "Vimshottari Dasha — Your Planetary Period Timeline",
        "body": (
            "The Vimshottari Dasha system divides your life into a sequence of planetary "
            "ruling periods totalling 120 years. Each Mahadasha (major period) is subdivided "
            "into Antardashas (sub-periods), allowing precise timing of life events.\n\n"
            "The current Mahadasha lord's placement and strength in your chart directly "
            "influences the themes, opportunities, and challenges you will experience during "
            "its rulership. Understanding your Dasha sequence empowers you to plan and prepare "
            "for major life transitions."
        ),
    },
    {
        "title": "D9 Navamsha — Soul Purpose & Marriage",
        "body": (
            "The Navamsha (D9) chart is considered the most important divisional chart in "
            "Vedic astrology. It reveals the deeper soul-level qualities of your planets, "
            "refining the natal chart's indications.\n\n"
            "For marriage specifically, the 7th house lord in both D1 and D9, the condition of "
            "Venus and Jupiter, and the Darakaraka planet (planet of lowest degree) collectively "
            "describe the nature, timing, and quality of your marital partnership."
        ),
    },
    {
        "title": "Career & Dharma — D10 Dashamsha",
        "body": (
            "The Dashamsha (D10) chart governs your professional life, public reputation, and "
            "career trajectory. The 10th house in both D1 and D10, its lord, and planets "
            "therein paint a vivid picture of your ideal career path and the recognition you "
            "are destined to achieve.\n\n"
            "Saturn's placement is particularly significant for career longevity, discipline, "
            "and the areas where sustained effort will yield lasting results."
        ),
    },
    {
        "title": "Wealth & Finances — Ashtakavarga & 2nd/11th Houses",
        "body": (
            "Wealth accumulation is primarily indicated by the 2nd house (stored wealth), the "
            "11th house (income and gains), and their lords. Jupiter's position amplifies "
            "financial abundance, while Saturn indicates wealth through disciplined effort.\n\n"
            "Your Ashtakavarga score in the relevant houses and signs tells us which planetary "
            "periods are most financially productive and which require cautious planning."
        ),
    },
    {
        "title": "Health & Longevity",
        "body": (
            "The 1st, 6th, 8th, and 12th houses — together with their lords and the condition "
            "of the Sun, Moon, and Mars — form the primary health indicators in Vedic astrology.\n\n"
            "This section highlights constitutional strengths and potential vulnerabilities, "
            "along with timing periods when heightened health awareness is advisable. Remedial "
            "measures such as dietary adjustments, yoga, and planetary gemstone recommendations "
            "are included where applicable."
        ),
    },
    {
        "title": "Transit Influences — Current & Upcoming",
        "body": (
            "Planetary transits (Gochar) over your natal chart create the dynamic timing layer "
            "of astrology. The current positions of Saturn, Jupiter, Rahu, and Ketu relative "
            "to your natal Moon sign are especially significant.\n\n"
            "Key upcoming transits worth tracking:\n"
            "  • Saturn's transit through your 7th house may bring relationship responsibilities\n"
            "  • Jupiter's movement into your 9th house opens a period of growth and opportunity\n"
            "  • Rahu-Ketu axis activating your 2nd/8th house axis highlights resource transformation"
        ),
    },
    {
        "title": "Remedial Measures & Recommendations",
        "body": (
            "Vedic astrology is not merely predictive — it is prescriptive. The following "
            "remedial measures are recommended to strengthen benefic planetary energies and "
            "mitigate challenging ones:\n\n"
            "  • Recite the Gayatri Mantra daily at sunrise\n"
            "  • Donate to charitable causes on Saturdays to appease Saturn\n"
            "  • Wear a natural blue sapphire (Neelam) in silver to enhance Saturn's discipline\n"
            "  • Perform Lakshmi Puja on Fridays for financial abundance\n"
            "  • Meditate regularly to strengthen your Moon (emotional balance)\n\n"
            "These recommendations are general guidelines. Consult with a qualified Vedic "
            "astrologer for personalised remedy programmes."
        ),
    },
    {
        "title": "Conclusion",
        "body": (
            "Your birth chart is a cosmic map of infinite potential. The planets do not "
            "compel — they impel. Awareness of your chart's strengths and challenges equips "
            "you to make conscious choices that align with your highest destiny.\n\n"
            "This report has been generated using traditional Vedic astrology principles "
            "combined with modern computational precision. We hope it serves as a meaningful "
            "guide on your journey.\n\n"
            "Wishing you clarity, prosperity, and spiritual growth."
        ),
    },
]

# Preview = first 30% of sections (minimum 2 sections)
_PREVIEW_SECTION_COUNT = max(2, len(_DUMMY_SECTIONS) // 3)


# ──────────────────────────────────────────────────────────────────────────────
# PDF builder (Phase 1 — dummy)
# ──────────────────────────────────────────────────────────────────────────────

def _build_full_report(birth_profile) -> Tuple[bytes, str]:
    """
    Phase 1: build a realistic-looking multi-page dummy PDF.
    Returns (pdf_bytes, preview_text).

    Phase 2: replace the body of this function with an Astro Report API call.
    The signature and return type must stay identical.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=26,
        spaceAfter=10,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    )
    cover_sub_style = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#4a4a8a"),
        spaceAfter=6,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        spaceAfter=8,
        textColor=colors.HexColor("#333333"),
    )

    story = []

    # ── Cover Page ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("✦ Vedic Astrology Report ✦", cover_title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a4a8a")))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"Prepared for: {birth_profile.display_name}", cover_sub_style))
    story.append(Paragraph(
        f"Birth details: {birth_profile.city}, {birth_profile.country_code}",
        cover_sub_style,
    ))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}",
        cover_sub_style,
    ))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "This report is prepared exclusively for the recipient named above and "
        "contains personalised Vedic astrological analysis based on traditional "
        "Jyotish principles.",
        body_style,
    ))
    story.append(PageBreak())

    # ── Report Sections ─────────────────────────────────────────────────────
    for section in _DUMMY_SECTIONS:
        story.append(Paragraph(section["title"], section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.2 * cm))
        # Preserve line breaks in body text
        for para_text in section["body"].split("\n\n"):
            story.append(Paragraph(para_text.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 0.5 * cm))

    # ── Footer Note ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a4a8a")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "© ParlezHub · This report is for personal use only. "
        "Redistribution without permission is prohibited.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=1),
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    # Build plain-text preview from the first N sections
    preview_parts = []
    for section in _DUMMY_SECTIONS[:_PREVIEW_SECTION_COUNT]:
        preview_parts.append(f"## {section['title']}\n\n{section['body']}")
    preview_text = "\n\n---\n\n".join(preview_parts)

    return pdf_bytes, preview_text


# ──────────────────────────────────────────────────────────────────────────────
# Supabase Storage upload
# ──────────────────────────────────────────────────────────────────────────────

def upload_report_to_supabase(pdf_bytes: bytes, birth_profile_id: int, report_type: str, is_preview: bool = False) -> str:
    """
    Upload the PDF to Supabase Storage (astro-reports bucket).
    Returns the permanent public URL.

    Path format: astro-reports/{birth_profile_id}/{report_type}{preview_suffix}-{uuid}.pdf
    """
    from core.supabase_client import get_admin_client

    bucket = getattr(settings, "SUPABASE_ASTRO_REPORTS_BUCKET", "astro-reports")
    suffix = "-preview" if is_preview else ""
    file_name = f"{report_type}{suffix}-{uuid.uuid4().hex}.pdf"
    storage_path = f"{birth_profile_id}/{file_name}"

    client = get_admin_client()
    client.storage.from_(bucket).upload(
        path=storage_path,
        file=pdf_bytes,
        file_options={"content-type": "application/pdf", "upsert": "false"},
    )

    # Construct public URL
    supabase_url = settings.SUPABASE_URL.rstrip("/")
    public_url = f"{supabase_url}/storage/v1/object/public/{bucket}/{storage_path}"
    logger.info(f"Uploaded report to Supabase Storage: {public_url}")
    return public_url


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def _build_preview_report(birth_profile) -> bytes:
    """
    Build a realistic-looking 1-2 page dummy PDF as a free preview.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    cover_title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=26,
        spaceAfter=10,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
    )
    cover_sub_style = ParagraphStyle(
        "CoverSub",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#4a4a8a"),
        spaceAfter=6,
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
        fontName="Helvetica-Bold",
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        spaceAfter=8,
        textColor=colors.HexColor("#333333"),
    )

    story = []

    # ── Cover Page ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("✦ Vedic Astrology Report ✦", cover_title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a4a8a")))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"Prepared for: {birth_profile.display_name}", cover_sub_style))
    story.append(Paragraph(
        f"Birth details: {birth_profile.city}, {birth_profile.country_code}",
        cover_sub_style,
    ))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%B %d, %Y')}",
        cover_sub_style,
    ))
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph(
        "This is a FREE PREVIEW containing the first 30% of your personalized "
        "Vedic Astrology Report. Purchase the full report to unlock all 20+ pages.",
        body_style,
    ))
    story.append(PageBreak())

    # ── Preview Sections ─────────────────────────────────────────────────────
    for section in _DUMMY_SECTIONS[:_PREVIEW_SECTION_COUNT]:
        story.append(Paragraph(section["title"], section_title_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
        story.append(Spacer(1, 0.2 * cm))
        # Preserve line breaks in body text
        for para_text in section["body"].split("\n\n"):
            story.append(Paragraph(para_text.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 0.5 * cm))

    # ── Preview Locked Banner ────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4a4a8a")))
    story.append(Spacer(1, 0.5 * cm))
    
    locked_title_style = ParagraphStyle(
        "LockedTitle",
        parent=styles["Heading3"],
        fontSize=12,
        spaceAfter=6,
        textColor=colors.HexColor("#4a4a8a"),
        fontName="Helvetica-Bold",
        alignment=1,
    )
    story.append(Paragraph("🔒 FULL REPORT LOCKED", locked_title_style))
    story.append(Paragraph(
        "This is a free preview containing the first 30% of your Vedic Astrology Report. "
        "To unlock the remaining 15+ pages of detailed analysis, chart divisional breakdown, "
        "transit predictions, and custom remedies, please complete your purchase on the website.",
        ParagraphStyle("LockedBody", parent=body_style, alignment=1),
    ))
    story.append(Spacer(1, 1 * cm))

    # ── Footer Note ─────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a4a8a")))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(
        "© ParlezHub · This report is for personal use only. "
        "Redistribution without permission is prohibited.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=1),
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_report(birth_profile) -> Tuple[bytes, str]:
    """
    Generate a full astrology report PDF for the given birth profile.

    Returns:
        (pdf_bytes, preview_text)
    """
    logger.info(
        f"Generating report for BirthProfile #{birth_profile.id} "
        f"({birth_profile.display_name})"
    )
    return _build_full_report(birth_profile)


def generate_preview(birth_profile) -> Tuple[bytes, str]:
    """
    Generate a 1-2 page preview astrology report PDF for the given birth profile.

    Returns:
        (pdf_bytes, preview_text)
    """
    logger.info(
        f"Generating preview report for BirthProfile #{birth_profile.id} "
        f"({birth_profile.display_name})"
    )
    pdf_bytes = _build_preview_report(birth_profile)
    
    # Build plain-text preview from the first N sections
    preview_parts = []
    for section in _DUMMY_SECTIONS[:_PREVIEW_SECTION_COUNT]:
        preview_parts.append(f"## {section['title']}\n\n{section['body']}")
    preview_text = "\n\n---\n\n".join(preview_parts)
    
    return pdf_bytes, preview_text
