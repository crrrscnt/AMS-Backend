from django.contrib import admin
from . import views
from django.urls import include, path, re_path
from rest_framework import routers
from rest_framework.permissions import AllowAny
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="bmstu_lab API",
        default_version='v0.1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0),
         name='schema-swagger-ui'),
    path(r'spaceobjects/', views.SpaceObjectList.as_view(),
         name='spaceobjects-list'),
    path(r'spaceobjects/<int:pk>/', views.SpaceObjectDetail.as_view(),
         name='spaceobject-detail'),
    path(r'spacecrafts/', views.SpacecraftList.as_view(),
         name='spacecrafts-list'),
    path(r'spacecrafts/<int:pk>/', views.SpacecraftDetail.as_view(),
         name='spacecraft-detail'),
    path(r'spaceobjects/<int:pk>/post/', views.add_image,
         name='setImg'),  # setImg
    path(r'spacecrafts/<int:pk>/save/', views.save_spacecraft,
         name='save-spacecraft'),
    path(r'spacecrafts/<int:pk>/moderate/', views.moderate_spacecraft,
         name='moderate-spacecraft'),
    path(r'flightobjects/<int:pk_spacecraft>/<int:pk_space_object>/',
         views.FlightObject.as_view(), name='flight_object'),
    path('api-auth/',
         include('rest_framework.urls', namespace='rest_framework')),
    # path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('user/update/', views.update_user, name='update_user'),
    # path(r'users/', views.UsersList.as_view(), name='users-list'),
]
