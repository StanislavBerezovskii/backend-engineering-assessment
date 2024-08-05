from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from api.urls import urlpatterns as api_urlpatterns


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(api_urlpatterns)),
]
