from django.db import models

# Create your models here.
class MyModel(models.Model):
    # Определение поля id типа AutoField как первичного ключа
    id = models.AutoField(primary_key=True)
    # Определение поля phone типа CharField с максимальной длиной в 20 символов
    phone = models.CharField(max_length=20)

    # Определение метода __str__, который будет использоваться для представления экземпляров модели в виде строки
    def __str__(self):
        return self.phone