from django.urls import path
from lab import views

urlpatterns = [
    path('', views.index, name='home'),
    path('detail/<int:detail_id>/', views.detail, name='detail'),
    # path('order/<int:order_id>/', views.order, name='order'),
    path('order/', views.order, name='order'),
    path('order/<int:order_id>/', views.order, name='order_detail'),  # Новый
    path('order/<int:order_id>/add_service/<int:service_id>/', views.order_add, name='order_add_service'),
    path('order/<int:order_id>/delete/', views.order_delete, name='order_delete'),
]
