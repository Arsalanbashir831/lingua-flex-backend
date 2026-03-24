from django.urls import path
from .views import BirthProfileView, NatalChartView, TransitView

urlpatterns = [
    path('birth-profile/', BirthProfileView.as_view(), name='astrology-birth-profile'),
    path('natal-chart/', NatalChartView.as_view(), name='astrology-natal-chart'),
    path('transits/', TransitView.as_view(), name='astrology-transits'),
]
