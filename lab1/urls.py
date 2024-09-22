from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='home'),
    path('detail/<int:detail_id>/', views.detail, name='detail'),
    path('order/<int:order_id>/', views.order, name='order'),
]