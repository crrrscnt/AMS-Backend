from django.db import models

# class AuthUser(models.Model):
#     password = models.CharField(max_length=127)
#     last_login = models.DateTimeField(blank=True, null=True)
#     username = models.CharField(unique=True, max_length=127)
#     first_name = models.CharField(max_length=127)
#     last_name = models.CharField(max_length=127)
#     email = models.CharField(max_length=127)
#     company = models.CharField(max_length=255)
#     is_staff = models.BooleanField(default=False)
#     is_superuser = models.BooleanField(default=False)
#     is_active = models.BooleanField(default=True)
#     date_joined = models.DateTimeField(auto_now_add=True)
#     # user_permissions
#
#     def __str__(self):
#         return f'{self.username}'
#
#     class Meta:
#         managed = False
#         db_table = 'auth_user'
#         verbose_name = 'Пользователь'
#         verbose_name_plural = 'Пользователи'
