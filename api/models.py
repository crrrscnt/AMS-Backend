from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, \
    UserManager, Group, Permission


class AuthUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Пользователь должен иметь email')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self.db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class AuthUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(max_length=127, unique=True)
    password = models.CharField(max_length=127)
    first_name = models.CharField(max_length=127)
    last_name = models.CharField(max_length=127)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(blank=True, null=True)

    USERNAME_FIELD = 'email'

    objects = AuthUserManager()

    groups = models.ManyToManyField(
        Group,
        related_name='authuser_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='authuser_set',
        blank=True
    )

    class Meta:
        db_table = 'custom_auth_user'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.email} {self.first_name}'


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
    spacecraft_name = models.CharField(max_length=127, null=True,
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
        return UncrewedSpacecraft.objects.filter(status='draft').first()

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
    create_date = models.DateField(null=True, blank=True,
                                   verbose_name="Дата создания заявки")
    completed_successfully = models.BooleanField(default=False,
                                      verbose_name="Завершено успешно")

    class Meta:
        db_table = 'spacecraft_spaceobject'
        unique_together = ('spacecraft', 'space_object')
        verbose_name = 'Объект полёта'
        verbose_name_plural = 'Объекты полёта'

    def __str__(self):
        return f'{self.spacecraft} - {self.space_object}'
