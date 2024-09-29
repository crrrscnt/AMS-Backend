from django.contrib import admin
from api import views
from django.urls import include, path
from rest_framework import routers
# from rest_framework.urlpatterns import format_suffix_patterns

router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path(r'space_objects/', views.SpaceObjectList.as_view(),
         name='space_objects-list'),
    path(r'space_objects/<int:pk>/', views.SpaceObjectDetail.as_view(),
         name='space_objects-detail'),
    # path(r'space_objects/<int:pk>/put/', views.put, name='space_objects-put'),
    path(r'orders/<int:pk>/', views.OrderDetail.as_view(), name='order-detail'),
    path(r'orders/', views.OrdersList.as_view(), name='orders-list'),

    path('api-auth/',
         include('rest_framework.urls', namespace='rest_framework')),
]

urlpatterns += [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]