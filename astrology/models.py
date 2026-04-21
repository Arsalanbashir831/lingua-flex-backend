from django.db import models
from core.models import User
from .fields import EncryptedCharField, EncryptedIntegerField


class BirthProfile(models.Model):
    """
    Stores a user's birth data for Vedic astrology calculations.
    One per user. The user's name is derived from the linked User model.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="birth_profile", null=True, blank=True
    )
    guest_name = EncryptedCharField(max_length=500, blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_guest_profiles", null=True, blank=True
    )
    birth_year = EncryptedIntegerField()
    birth_month = EncryptedIntegerField()
    birth_day = EncryptedIntegerField()
    birth_hour = EncryptedIntegerField()
    birth_minute = EncryptedIntegerField()
    city = EncryptedCharField(max_length=500)
    country_code = EncryptedCharField(max_length=100)  # e.g. "IN", "US"

    # Populated automatically after the first natal chart API call.
    # Derived from calculation_info.location.timezone in the API response.
    timezone_str = EncryptedCharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def display_name(self):
        if self.user:
            return self.user.get_full_name() or self.user.email
        return self.guest_name or f"Guest Chart {self.id}"

    def __str__(self):
        return f"Birth Profile: {self.display_name} ({self.city}, {self.country_code})"


class NatalChartCache(models.Model):
    """
    Caches the static (birth-fixed) astrology data for a user.
    D1 and D9 charts, planet positions, nakshatras etc. never change —
    so we compute once and store forever.
    """

    birth_profile = models.OneToOneField(
        BirthProfile, on_delete=models.CASCADE, related_name="natal_cache"
    )
    # Raw JSON from POST /vedic/birth-details
    birth_details_data = models.JSONField()
    # Raw JSON from POST /vedic/divisional-chart (requesting D1 + D9)
    divisional_data = models.JSONField()

    # Extended Data for AI Generation
    kp_data = models.JSONField(null=True, blank=True)
    dasha_data = models.JSONField(null=True, blank=True)
    ashtakvarga_data = models.JSONField(null=True, blank=True)

    cached_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Natal Cache: {self.birth_profile.display_name} (cached at {self.cached_at})"
        )


class TransitCache(models.Model):
    """
    Caches today's transit data for a user.
    Invalidated when the current local date (in the user's timezone)
    differs from cached_for_date — checked on every page load (no cron).
    """

    birth_profile = models.OneToOneField(
        BirthProfile, on_delete=models.CASCADE, related_name="transit_cache"
    )
    # Raw JSON from POST /vedic/transit
    transit_data = models.JSONField()
    # The local calendar date (in user's timezone) this transit data is valid for
    cached_for_date = models.DateField()
    cached_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Transit Cache: {self.birth_profile.display_name} for {self.cached_for_date}"
        )


class NakshatraPredictionCache(models.Model):
    """
    Caches today's nakshatra predictions (tarabala, predictions, etc) for a user.
    Invalidated when the current local date (in the user's timezone)
    differs from cached_for_date.
    """

    birth_profile = models.OneToOneField(
        BirthProfile, on_delete=models.CASCADE, related_name="nakshatra_prediction_cache"
    )
    # Raw JSON from POST /vedic/nakshatra-predictions
    prediction_data = models.JSONField()
    # The local calendar date (in user's timezone) this prediction data is valid for
    cached_for_date = models.DateField()
    cached_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Nakshatra Prediction Cache: {self.birth_profile.display_name} for {self.cached_for_date}"
        )


class AstrologyInsight(models.Model):
    """
    Caches the AI-generated astrological readings to save API costs
    and provide instant page loads.
    """

    CATEGORY_CHOICES = (
        ("mental_health", "Mental Health"),
        ("marriage", "Marriage Timing"),
        ("prosperity_sav", "Prosperity & Career (SAV)"),
        ("medical", "Medical Astrology"),
        ("btr", "Birth Time Rectification"),
        ("parasari", "Parasari Relationships"),
        ("navatara", "Navatara (Nine Stars)"),
        ("darakaraka", "Spouse Profile (Jaimini)"),
        ("planetary_states", "Planetary Avatars & States"),
        ("benefic_planets", "Benefic Planets"),
        ("malefic_planets", "Malefic Planets"),
        ("chart_analysis", "Chart Analysis"),
        ("astro_energy", "12-Dimensional Astro Energy"),
        ("rashi_planets", "Meaning of the Rashi Planets"),
        ("lagna_lord", "Your Lagna Lord Position"),
        ("challenges", "Challenges and Learning"),
    )

    birth_profile = models.ForeignKey(
        BirthProfile, on_delete=models.CASCADE, related_name="insights"
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    insight_text = models.TextField()
    is_transit_dependent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("birth_profile", "category")

    def __str__(self):
        return (
            f"Insight ({self.get_category_display()}): {self.birth_profile.display_name}"
        )


class AIPromptConfiguration(models.Model):
    """
    Stores a superadmin-configurable user prompt that gets appended to the base
    Python system prompt for a given category.
    """

    category = models.CharField(
        max_length=50,
        choices=AstrologyInsight.CATEGORY_CHOICES,
        unique=True,
        help_text="The astrology insight category this prompt applies to.",
    )
    user_prompt = models.TextField(
        help_text="This text will be appended to the end of the AI prompt to guide the AI's focus.",
        blank=True,
    )
    is_active = models.BooleanField(
        default=True, help_text="Disable to ignore this custom prompt."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prompt Config ({self.get_category_display()})"


class AstrologyDashboardAccess(models.Model):
    """
    Tracks which teacher has been granted access to which student's
    astrology dashboard. A student can grant access to any teacher
    who has an active astrology gig.
    """

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="astrology_access_grants",
        help_text="The student who owns the dashboard.",
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="astrology_access_received",
        help_text="The teacher who has been granted access.",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "teacher")
        verbose_name = "Astrology Dashboard Access"
        verbose_name_plural = "Astrology Dashboard Accesses"

    def __str__(self):
        return f"{self.teacher.email} → can view → {self.student.email}'s dashboard"


class AstrologyChat(models.Model):
    """
    Stores a multi-turn conversation between a user and Gemini AI
    scoped to a specific astrology insight category.

    Each row is a single message. `role` mirrors the Gemini API convention:
      - 'user'  — a message sent by the authenticated user
      - 'model' — a response generated by Gemini

    History is capped at the latest 10 messages per (birth_profile, category)
    pair to keep Gemini context windows manageable.
    """

    ROLE_USER = "user"
    ROLE_MODEL = "model"
    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_MODEL, "Model"),
    )

    birth_profile = models.ForeignKey(
        BirthProfile,
        on_delete=models.CASCADE,
        related_name="chats",
    )
    category = models.CharField(
        max_length=50,
        choices=AstrologyInsight.CATEGORY_CHOICES,
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Astrology Chat Message"
        verbose_name_plural = "Astrology Chat Messages"

    def __str__(self):
        return (
            f"[{self.role.upper()}] {self.birth_profile.display_name} / "
            f"{self.category}: {self.content[:60]}"
        )
