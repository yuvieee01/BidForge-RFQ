from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/rfq/', include('rfq.urls')),
    path('api/bids/', include('bids.urls')),
    path('api/auction/', include('auctions.urls')),
    path('api/logs/', include('logs.urls')),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
