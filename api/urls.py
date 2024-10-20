from django.urls import path, include
from . import views

urlpatterns = [
    path(r'spaceobjects/', views.SpaceObjectList.as_view(),
         name='spaceobjects-list'),
    path(r'spaceobjects/<int:pk>/', views.SpaceObjectDetail.as_view(),
         name='spaceobject-detail'),
    path(r'spaceobjects/<int:pk>/post/', views.add_image,
         name='setImg'),  # setImg

    path(r'spacecrafts/', views.SpacecraftList.as_view(),
         name='spacecrafts-list'),
    path(r'spacecrafts/<int:pk>/', views.SpacecraftDetail.as_view(),
         name='spacecraft-detail'),
    path(r'spacecrafts/<int:pk>/save/', views.save_spacecraft,
         name='save-spacecraft'),
    path(r'spacecrafts/<int:pk>/moderate/', views.moderate_spacecraft,
         name='moderate-spacecraft'),

    path(r'flightobjects/<int:pk_spacecraft>/<int:pk_space_object>/',
         views.FlightObject.as_view(), name='flight_object'),

    path('user/register/', views.UserRegistration.as_view(), name='user-register'),
    path('user/<int:user_id>/put/', views.UserPut.as_view(), name='user-put'),
    path('user/login/', views.LoginView.as_view(), name='login'),
    path('user/logout/', views.LogoutView.as_view(), name='logout'),
    # path('user/', views.UserList.as_view(), name='user-list'),
    # path('user/<int:user_id>/', views.UserDetail.as_view(), name='user-detail'),
    # path('user/<int:user_id>/delete/', views.UserDelete.as_view(), name='user-delete'),
    # path('user/test/', views.UserTest.as_view(), name='user-test'),

    path('api-auth/',
         include('rest_framework.urls', namespace='rest_framework')),
]
