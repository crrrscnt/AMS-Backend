from django.contrib import admin
from django.urls import path, include
from lab2 import views
from lab2.views import page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lab2.urls')),
]

handler404 = page_not_found
