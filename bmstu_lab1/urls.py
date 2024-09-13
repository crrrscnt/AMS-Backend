from django.contrib import admin
from django.urls import path, include
from lab1 import views
from lab1.views import page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lab1.urls')),
]

handler404 = page_not_found
