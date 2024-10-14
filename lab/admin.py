from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject, \
    AuthUser

admin.site.register(SpaceObject)
admin.site.register(UncrewedSpacecraft)
admin.site.register(FlightSpaceObject)
# admin.site.register(CustomUser, UserAdmin)

from .forms import AuthUserCreationForm, AuthUserChangeForm
from .models import AuthUser

class AuthUserAdmin(UserAdmin):
    add_form = AuthUserCreationForm
    form = AuthUserChangeForm

    model = AuthUser

    list_display = ('username', 'is_staff', 'is_superuser', 'last_login',)
    list_filter = ('is_staff', 'is_superuser')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'last_login')}),
        ('Permissions', {'fields': ('is_staff',
         'is_superuser')})
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('username',)
    ordering = ('username',)

admin.site.register(AuthUser, AuthUserAdmin)
