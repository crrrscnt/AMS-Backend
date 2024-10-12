from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('detail/<int:detail_id>/', views.detail, name='detail'),
    path('spacecraft/<int:spacecraft_id>/', views.spacecraft,
         name='spacecraft'),
    path('add_object', views.add_object, name='add_object'),
    path('delete_spacecraft', views.delete_spacecraft,
         name='delete_spacecraft')
]
