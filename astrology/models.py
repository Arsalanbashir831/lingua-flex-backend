from django.db import models
from core.models import User


class BirthProfile(models.Model):
    """
    Stores a user's birth data for Vedic astrology calculations.
    One per user. The user's name is derived from the linked User model.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='birth_profile'
    )
    birth_year = models.IntegerField()
    birth_month = models.IntegerField()
    birth_day = models.IntegerField()
    birth_hour = models.IntegerField()
    birth_minute = models.IntegerField()
    city = models.CharField(max_length=200)
    country_code = models.CharField(max_length=5)  # e.g. "IN", "US"

    # Populated automatically after the first natal chart API call.
    # Derived from calculation_info.location.timezone in the API response.
    timezone_str = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Birth Profile: {self.user.email} ({self.city}, {self.country_code})"


class NatalChartCache(models.Model):
    """
    Caches the static (birth-fixed) astrology data for a user.
    D1 and D9 charts, planet positions, nakshatras etc. never change —
    so we compute once and store forever.
    """
    birth_profile = models.OneToOneField(
        BirthProfile,
        on_delete=models.CASCADE,
        related_name='natal_cache'
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
        return f"Natal Cache: {self.birth_profile.user.email} (cached at {self.cached_at})"


class TransitCache(models.Model):
    """
    Caches today's transit data for a user.
    Invalidated when the current local date (in the user's timezone)
    differs from cached_for_date — checked on every page load (no cron).
    """
    birth_profile = models.OneToOneField(
        BirthProfile,
        on_delete=models.CASCADE,
        related_name='transit_cache'
    )
    # Raw JSON from POST /vedic/transit
    transit_data = models.JSONField()
    # The local calendar date (in user's timezone) this transit data is valid for
    cached_for_date = models.DateField()
    cached_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transit Cache: {self.birth_profile.user.email} for {self.cached_for_date}"


class AstrologyInsight(models.Model):
    """
    Caches the AI-generated astrological readings to save API costs
    and provide instant page loads.
    """
    CATEGORY_CHOICES = (
        ('mental_health', 'Mental Health'),
        ('marriage', 'Marriage Timing'),
        ('prosperity_sav', 'Prosperity & Career (SAV)'),
        ('medical', 'Medical Astrology'),
        ('btr', 'Birth Time Rectification'),
        ('parasari', 'Parasari Relationships'),
        ('navatara', 'Navatara (Nine Stars)'),
        ('darakaraka', 'Spouse Profile (Jaimini)'),
        ('planetary_states', 'Planetary Avatars & States'),
    )

    birth_profile = models.ForeignKey(
        BirthProfile,
        on_delete=models.CASCADE,
        related_name='insights'
    )
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    insight_text = models.TextField()
    is_transit_dependent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('birth_profile', 'category')

    def __str__(self):
        return f"Insight ({self.get_category_display()}): {self.birth_profile.user.email}"


class AIPromptConfiguration(models.Model):
    """
    Stores a superadmin-configurable user prompt that gets appended to the base
    Python system prompt for a given category.
    """
    category = models.CharField(
        max_length=50, 
        choices=AstrologyInsight.CATEGORY_CHOICES,
        unique=True,
        help_text="The astrology insight category this prompt applies to."
    )
    user_prompt = models.TextField(
        help_text="This text will be appended to the end of the AI prompt to guide the AI's focus.",
        blank=True
    )
    is_active = models.BooleanField(default=True, help_text="Disable to ignore this custom prompt.")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Prompt Config ({self.get_category_display()})"
