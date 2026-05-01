# Django
from django.contrib import admin
from django.urls import path, include

def trigger_error(request):
    division_by_zero = 1 / 0

urlpatterns = [
    path('2ß03ek02qw-sentry-debug/', trigger_error),
    path('ie1ß20iß0q-admin/', admin.site.urls),
    path('api/', include('auth_app.api.urls')),
    path('api/', include('board_app.api.urls')),
]