from django.urls import path
from .views import (
    BirthProfileView, NatalChartView, TransitView, DashaView, NakshatraPredictionView,
    AstrologyInsightView, AstrologyInsightChatView,
    AstrologyAccessView, AstrologyAccessRevokeView, TeacherStudentDashboardsView,
    GuestProfileListView, GuestProfileDetailView, FestivalCalendarView,
    ReportStatusView, InitiateReportPaymentView, ConfirmReportPaymentView, DownloadReportView,
)

urlpatterns = [
    path('birth-profile/', BirthProfileView.as_view(), name='astrology-birth-profile'),
    path('natal-chart/', NatalChartView.as_view(), name='astrology-natal-chart'),
    path('transits/', TransitView.as_view(), name='astrology-transits'),
    path('dasha/', DashaView.as_view(), name='astrology-dasha'),
    path('nakshatra-predictions/', NakshatraPredictionView.as_view(), name='astrology-nakshatra-predictions'),
    path('insights/<str:category>/', AstrologyInsightView.as_view(), name='astrology-insight'),
    path('insights/<str:category>/chat/', AstrologyInsightChatView.as_view(), name='astrology-insight-chat'),

    # Guest Profiles (Astrologer Workspace)
    path('guest-profiles/', GuestProfileListView.as_view(), name='astrology-guest-profiles'),
    path('guest-profiles/<int:pk>/', GuestProfileDetailView.as_view(), name='astrology-guest-profile-detail'),

    # Dashboard access management
    path('access/', AstrologyAccessView.as_view(), name='astrology-access-manage'),
    path('access/<str:teacher_id>/', AstrologyAccessRevokeView.as_view(), name='astrology-access-revoke'),
    path('teacher/students/', TeacherStudentDashboardsView.as_view(), name='astrology-teacher-student-list'),

    # Festival calendar
    path('festival-calendar/', FestivalCalendarView.as_view(), name='astrology-festival-calendar'),

    # ── Astrology Reports ────────────────────────────────────────────────────
    # Note: purchase/ and confirm-payment/ MUST be registered before
    # <report_type>/download/ to avoid the wildcard matching them.
    path('reports/', ReportStatusView.as_view(), name='astrology-reports'),
    path('reports/purchase/', InitiateReportPaymentView.as_view(), name='astrology-report-purchase'),
    path('reports/confirm-payment/', ConfirmReportPaymentView.as_view(), name='astrology-report-confirm'),
    path('reports/<str:report_type>/download/', DownloadReportView.as_view(), name='astrology-report-download'),
]


