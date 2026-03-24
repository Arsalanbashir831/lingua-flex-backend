from django.contrib import admin
from .models import BirthProfile, NatalChartCache, TransitCache


@admin.register(BirthProfile)
class BirthProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country_code', 'timezone_str', 'created_at']
    search_fields = ['user__email', 'city', 'country_code']
    readonly_fields = ['timezone_str', 'created_at', 'updated_at']


@admin.register(NatalChartCache)
class NatalChartCacheAdmin(admin.ModelAdmin):
    list_display = ['birth_profile', 'cached_at']
    readonly_fields = ['birth_profile', 'birth_details_data', 'divisional_data', 'cached_at']


@admin.register(TransitCache)
class TransitCacheAdmin(admin.ModelAdmin):
    list_display = ['birth_profile', 'cached_for_date', 'cached_at']
    readonly_fields = ['birth_profile', 'transit_data', 'cached_for_date', 'cached_at']
