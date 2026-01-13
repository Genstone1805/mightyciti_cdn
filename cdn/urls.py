from django.contrib import admin
from django.urls import path

from django.urls import path
from django.conf import settings
from .views import cdn_image
from django.conf.urls.static import static

urlpatterns = [
    path('cdn/<path:path>', cdn_image, name="cdn"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
