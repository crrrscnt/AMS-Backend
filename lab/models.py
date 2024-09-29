from django.db import models
from django.contrib.auth.models import User


# Модель "Космические объекты"
class SpaceObject(models.Model):
    class Meta:
        db_table = 'SpaceObject'

    name = models.CharField(max_length=127, verbose_name="Наименование")
    uncrewed_spacecraft = models.CharField(max_length=127, blank=True, verbose_name="АМС")
    description = models.TextField(verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True,
                                verbose_name='Цена')
    is_active = models.BooleanField(default=True,
                                    verbose_name="Статус (активен)")
    scheduled_at = models.DateField(null=True, blank=True,
                                    verbose_name="Запланированная дата")
    image_url = models.URLField(verbose_name="URL к изображению")

    def __str__(self):
        return self.name


# Модель "АМС"
class UncrewedSpacecraft(models.Model):
    class Meta:
        db_table = 'UncrewedSpacecraft'

    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('deleted', 'Удалён'),
        ('formed', 'Сформирован'),
        ('completed', 'Завершён'),
        ('rejected', 'Отклонён'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='draft', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name="Дата создания")
    formed_at = models.DateTimeField(null=True, blank=True,
                                     verbose_name="Дата формирования")
    completed_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name="Дата завершения")
    space_objects = models.ManyToManyField(SpaceObject, through='Flight')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                blank=True,
                                related_name='created_uncrewed_spacecrafts',
                                verbose_name="Создатель заявки")
    moderator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="Модератор", null=True, blank=True)

    def __str__(self):
        return f"Заявка № {self.pk} ({self.status})"

    #def __str__(self):
    #    return f"Заявка № {self.pk} ({self.status})"

    @staticmethod
    def get_draft_request(user):
        return UncrewedSpacecraft.objects.filter(user=user, status='draft').first()

    def get_object_count(self):
        return self.space_objects.count()

    def mark_as_deleted(self):
        self.status = 'deleted'
        self.save(update_fields=['status'])


# Модель связи "Полёт к космическим объектам" - "Космические объекты"
class Flight(models.Model):
    uncrewed_spacecraft = models.ForeignKey(UncrewedSpacecraft, on_delete=models.CASCADE)
    space_object = models.ForeignKey(SpaceObject, on_delete=models.CASCADE)
    #quantity = models.PositiveIntegerField(verbose_name="Количество услуг")
    # order = models.PositiveIntegerField(verbose_name="Порядок")
    # is_main = models.BooleanField(default=False, verbose_name="Главный")
    create_date = models.DateField(null=True, blank=True,
                                   verbose_name="Дата создания заявки")

    class Meta:
        db_table = 'Flight'
        unique_together = ('uncrewed_spacecraft', 'space_object')

    def __str__(self):
        return str(self.id)
