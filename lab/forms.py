from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import AuthUser

class AuthUserCreationForm(UserCreationForm):

    class Meta:
        model = AuthUser
        fields = ('username',)

class AuthUserChangeForm(UserChangeForm):

    class Meta:
        model = AuthUser
        fields = ('username',)
