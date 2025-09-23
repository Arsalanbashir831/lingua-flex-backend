"""
URL configuration for rag_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from .admin_site import admin_site

urlpatterns = [
    path('django-admin/', admin_site.urls),  # Use custom admin site
    path('admin/', admin.site.urls),  # Keep default admin as backup
    path('api/', include('core.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/bookings/', include('bookings.urls')),
    path('api/blogs/', include('blogs.urls')),  # Added blogs URLs
    path('api/campaigns/', include('campaigns.urls')),  # Added campaigns URLs
    path('api/payments/', include('stripe_payments.urls')),  # Added Stripe payments URLs
]

urlpatterns += [
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
