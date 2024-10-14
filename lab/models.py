from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, \
    UserManager, User
from django.db import models


class AuthUserManager(UserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Необходимое поле')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_staffuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Модератор должен иметь поле is_staff=True.')

        return self.create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(
                'Суперпользователь должен иметь поле is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь поле is_superuser=True.')

        return self.create_user(username, password, **extra_fields)


class AuthUser(AbstractBaseUser, PermissionsMixin):
    password = models.CharField(max_length=127)
    username = models.CharField(unique=True, max_length=127)
    first_name = models.CharField(max_length=127)
    last_name = models.CharField(max_length=127)
    email = models.EmailField(max_length=127)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'username'
    # REQUIRED_FIELDS = ['email']

    objects = AuthUserManager()

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.username}'

    def set_password(self, raw_password):
        """
        Переопределяем метод set_password для использования хеширования Django.
        """
        self.password = make_password(raw_password)
        self._password = raw_password


    # Модель "Космические объекты"
class SpaceObject(models.Model):
    name = models.CharField(max_length=127, verbose_name="Космический объект")
    description = models.TextField(verbose_name="Описание")
    is_active = models.BooleanField(default=True,
                                    verbose_name="Статус (активен)")
    image_url = models.URLField(verbose_name="URL к изображению")

    class Meta:
        db_table = 'object'
        verbose_name = 'Космический объект'
        verbose_name_plural = 'Космические объекты'

    def __str__(self):
        return self.name


# Модель "Полёт к космическим объектам"
class UncrewedSpacecraft(models.Model):
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
                                      verbose_name="Дата создания черновика")
    formed_at = models.DateTimeField(null=True, blank=True,
                                     verbose_name="Дата формирования")
    completed_at = models.DateTimeField(null=True, blank=True,
                                        verbose_name="Дата завершения")
    user = models.ForeignKey(AuthUser, on_delete=models.DO_NOTHING)
    creator = models.ForeignKey('AuthUser', on_delete=models.DO_NOTHING,
                                null=True,
                                blank=True,
                                related_name='created_spacecrafts',
                                verbose_name="Создатель")
    moderator = models.ForeignKey('AuthUser', on_delete=models.DO_NOTHING,
                                  null=True,
                                  blank=True,
                                  related_name='moderated_spacecrafts',
                                  verbose_name="Модератор")

    class Meta:
        db_table = 'spacecraft'
        verbose_name = 'Автоматическая межпланетная станция'
        verbose_name_plural = 'Автоматические межпланетные станции'

    def __str__(self):
        return f"Полёт № {self.pk} ({self.status})"

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
                                   on_delete=models.DO_NOTHING,
                                   related_name='space_objects')
    space_object = models.ForeignKey(SpaceObject, on_delete=models.DO_NOTHING,
                                     related_name='spacecrafts')
    # user = models.ForeignKey('AuthUser', on_delete=models.DO_NOTHING,
    #                         null=True, blank=False,
    #                         verbose_name="Создатель АМС")
    create_date = models.DateField(null=True, blank=True,
                                   verbose_name="Дата создания заявки")
    is_priority = models.BooleanField(default=False,
                                      verbose_name="Приоритетный")

    class Meta:
        db_table = 'spacecraft_spaceobject'
        unique_together = ('spacecraft', 'space_object')
        verbose_name = 'Объект полёта'
        verbose_name_plural = 'Объекты полёта'

    def __str__(self):
        # return str(self.id)
        return f'{self.spacecraft} - {self.space_object}'
