from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
import redis
from django.conf import settings
from django.middleware.csrf import get_token

User = get_user_model()
session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT)


class SessionAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Извлечение session_id из куки
        # session_id = request.COOKIES.get('session_id')
        #
        # if session_id:
        #     # Получаем username по session_id из Redis
        #     username = session_storage.get(session_id)
        #
        #     if username:
        #         try:
        #             # Извлечение пользователя по username
        #             user = User.objects.get(username=username.decode('utf-8'))
        #             request.user = user  # Аутентифицируем пользователя
        #         except User.DoesNotExist:
        #             request.user = AnonymousUser()
        #     else:
        #         request.user = AnonymousUser()
        # else:
        #     request.user = AnonymousUser()
        user = session_storage.get('session_id')
        if user:
            request.user = user
            # Set the CSRF cookie after successful authentication
            request.META['CSRF_COOKIE'] = True
            request.META['CSRF_TOKEN'] = get_token(request)
        else:
            request.user = AnonymousUser()
