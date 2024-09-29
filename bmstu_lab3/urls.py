from django.contrib import admin
from django.urls import path, include
from lab import views
from lab.views import page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lab.urls')),
    path('api/', include('api.urls')),
]

handler404 = page_not_found
