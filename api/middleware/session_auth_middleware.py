from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
import redis
from django.conf import settings
from django.middleware.csrf import get_token
from api.models import AuthUser

session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT)


class SessionAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # # Сначала дать возможность другим middleware (например, CSRF) обработать запрос
        # super().process_request(request)
        # print(f"Cookies: {request.COOKIES}")  # Вывод всех cookies
        session_id = request.COOKIES.get('session_id')

        if session_id:
            # Получаем username по session_id из Redis
            email_bytes = session_storage.get(session_id)
            if email_bytes:
                email = email_bytes.decode('utf-8')
                try:
                    user = AuthUser.objects.get(email=email)
                    # print(f"user (session_auth_middleware): {user}")
                    request.user = user
                    # Устанавливаем CSRF-токен
                    csrf_token = get_token(request)
                    # print(f"CSRF Token: {csrf_token}")  # Отладка
                    # request.META['CSRF_COOKIE'] = True
                    # request.META['CSRF_TOKEN'] = csrf_token
                except AuthUser.DoesNotExist:
                    request.user = AnonymousUser()
            else:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()