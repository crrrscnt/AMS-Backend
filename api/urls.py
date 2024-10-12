from django.contrib import admin
from . import views
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path(r'spaceobjects/', views.SpaceObjectList.as_view(),
         name='spaceobjects-list'),
    path(r'spaceobjects/<int:pk>/', views.SpaceObjectDetail.as_view(),
         name='spaceobject-detail'),
    path(r'spacecrafts/', views.SpacecraftList.as_view(),
         name='spacecrafts-list'),
    path(r'spacecrafts/<int:pk>/', views.SpacecraftDetail.as_view(),
         name='spacecraft-detail'),
    path(r'spaceobjects/<int:pk>/post/', views.add_image,
         name='setImg'), # setImg
    path(r'spacecrafts/<int:pk>/save/', views.save_spacecraft,
         name='save-spacecraft'),
    path(r'spacecrafts/<int:pk>/moderate/', views.moderate_spacecraft,
         name='moderate-spacecraft'),
    path(r'flightobjects/<int:pk_spacecraft>/<int:pk_space_object>/',
         views.FlightObject.as_view(), name='flight_object'),
    path('api-auth/',
         include('rest_framework.urls', namespace='rest_framework')),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('user/update/', views.update_user, name='update_user'),
    path(r'users/', views.UsersList.as_view(), name='users-list')
]
