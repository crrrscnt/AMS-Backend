from .models import AuthUser
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
import redis

session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT)


def authenticate_user(request):
    session_id = request.COOKIES.get('session_id')
    print(f"Session ID: {session_id}")

    if session_id:
        try:
            email = session_storage.get(session_id).decode('utf-8')
            user = AuthUser.objects.get(email=email)
            print(f"User (authenticate_user()): {user}")
        except AttributeError:
            user = AnonymousUser()
    else:
        user = AnonymousUser()
    return user
