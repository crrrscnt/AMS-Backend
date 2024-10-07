from django.db import models
from django.contrib.auth.models import User


# Модель "Космические объекты"
class SpaceObject(models.Model):
    class Meta:
        db_table = 'object'
        verbose_name = 'Космический объект'
        verbose_name_plural = 'Космические объекты'

    name = models.CharField(max_length=127, verbose_name="Космический объект")
    description = models.TextField(verbose_name="Описание")
    is_active = models.BooleanField(default=True,
                                    verbose_name="Статус (активен)")
    image_url = models.URLField(verbose_name="URL к изображению")

    def __str__(self):
        return self.name


# Модель "Полёт к космическим объектам"
class UncrewedSpacecraft(models.Model):
    class Meta:
        db_table = 'spacecraft'
        verbose_name = 'Автоматическая межпланетная станция'
        verbose_name_plural = 'Автоматические межпланетные станции'

    spacecraft_name = models.CharField(max_length=127,
                                       verbose_name='Название АМС')
    spacecraft_description = models.TextField(null=True, blank=True,
                                              verbose_name="Описание АМС")
    scheduled_at = models.DateField(null=True, blank=True,
                                    verbose_name="Запланированная дата")
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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                blank=True,
                                related_name='created_spacecrafts',
                                verbose_name="Создатель")
    moderator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  blank=True,
                                  related_name='moderated_spacecrafts',
                                  verbose_name="Модератор")

    def __str__(self):
        return f"Полёт № {self.pk} ({self.spacecraft_name})"

    @staticmethod
    def get_draft_request(user):
        return UncrewedSpacecraft.objects.filter(user=user,
                                                 status='draft').first()

    def get_object_count(self):
        return self.space_objects.count()

    def mark_as_deleted(self):
        self.status = 'deleted'
        self.save(update_fields=['status'])


# Модель связи "Полёт к космическим объектам" - "Космические объекты"
class FlightSpaceObject(models.Model):
    spacecraft = models.ForeignKey(UncrewedSpacecraft,
                                   on_delete=models.CASCADE,
                                   related_name='space_objects')
    space_object = models.ForeignKey(SpaceObject, on_delete=models.CASCADE,
                                     related_name='spacecrafts')
    # quantity = models.PositiveIntegerField(verbose_name="Количество")
    # order = models.PositiveIntegerField(verbose_name="Порядок")
    # is_main = models.BooleanField(default=False, verbose_name="Главный")
    create_date = models.DateField(null=True, blank=True,
                                   verbose_name="Дата создания заявки")

    class Meta:
        db_table = 'spacecraft_spaceobject'
        unique_together = ('spacecraft', 'space_object')
        verbose_name = 'Объект полёта'
        verbose_name_plural = 'Объекты полёта'

    def __str__(self):
        # return str(self.id)
        return f'{self.spacecraft} - {self.space_object}'
