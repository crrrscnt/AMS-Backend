from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('detail/<int:detail_id>/', views.detail, name='detail'),
    # path('orders/', views.get_order, name='orders'),

    path('order/', views.order_view, name='order'),
    path('add_to_order/<int:service_id>/', views.add_to_order, name='add_to_order'),
]
