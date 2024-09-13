from django.contrib import admin

# Register your models here.
from .models import MyModel
# Регистрация модели MyModel для административного сайта
admin.site.register(MyModel)