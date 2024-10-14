# Generated by Django 4.1 on 2024-10-12 13:08

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import lab.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=127)),
                ('username', models.CharField(max_length=127, unique=True)),
                ('first_name', models.CharField(max_length=127)),
                ('last_name', models.CharField(max_length=127)),
                ('email', models.EmailField(max_length=127)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('date_joined', models.DateTimeField(auto_now=True)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
                'db_table': 'auth_user',
            },
            managers=[
                ('objects', lab.models.AuthUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='SpaceObject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=127, verbose_name='Космический объект')),
                ('description', models.TextField(verbose_name='Описание')),
                ('is_active', models.BooleanField(default=True, verbose_name='Статус (активен)')),
                ('image_url', models.URLField(verbose_name='URL к изображению')),
            ],
            options={
                'verbose_name': 'Космический объект',
                'verbose_name_plural': 'Космические объекты',
                'db_table': 'object',
            },
        ),
        migrations.CreateModel(
            name='UncrewedSpacecraft',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('spacecraft_name', models.CharField(max_length=127, verbose_name='Название АМС')),
                ('spacecraft_description', models.TextField(blank=True, null=True, verbose_name='Описание АМС')),
                ('scheduled_at', models.DateField(blank=True, null=True, verbose_name='Запланированная дата')),
                ('status', models.CharField(choices=[('draft', 'Черновик'), ('deleted', 'Удалён'), ('formed', 'Сформирован'), ('completed', 'Завершён'), ('rejected', 'Отклонён')], default='draft', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания черновика')),
                ('formed_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата формирования')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')),
                ('creator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='created_spacecrafts', to=settings.AUTH_USER_MODEL, verbose_name='Создатель')),
                ('moderator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='moderated_spacecrafts', to=settings.AUTH_USER_MODEL, verbose_name='Модератор')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Автоматическая межпланетная станция',
                'verbose_name_plural': 'Автоматические межпланетные станции',
                'db_table': 'spacecraft',
            },
        ),
        migrations.CreateModel(
            name='FlightSpaceObject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateField(blank=True, null=True, verbose_name='Дата создания заявки')),
                ('is_priority', models.BooleanField(default=False, verbose_name='Приоритетный')),
                ('space_object', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='spacecrafts', to='lab.spaceobject')),
                ('spacecraft', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='space_objects', to='lab.uncrewedspacecraft')),
            ],
            options={
                'verbose_name': 'Объект полёта',
                'verbose_name_plural': 'Объекты полёта',
                'db_table': 'spacecraft_spaceobject',
                'unique_together': {('spacecraft', 'space_object')},
            },
        ),
    ]
