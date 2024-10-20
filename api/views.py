from django.conf import settings
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from drf_spectacular.utils import extend_schema, OpenApiParameter, \
    OpenApiResponse
from rest_framework import viewsets, status, request
from rest_framework.authentication import SessionAuthentication, \
    BasicAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, \
    authentication_classes
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, \
    IsAuthenticated
from django.views.decorators.csrf import csrf_exempt
from datetime import date

from .get_user import authenticate_user
from .models import AuthUser, UncrewedSpacecraft, SpaceObject, \
    FlightSpaceObject
from .permissions import IsAdmin, IsManager, IsAuthenticatedUser, IsCreator
from .serializers import (SpaceObjectSerializer,
                          SpacecraftSerializer,
                          UserSerializer,
                          UserUpdateSerializer,
                          FlightSpaceObjectSerializer, LoginSerializer,
                          SpacecraftSerializerForList)
from .minio import *
import redis
import uuid

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST,
                                    port=settings.REDIS_PORT)


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


class SpaceObjectList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [AllowAny]

    spaceobject_model_class = SpaceObject
    spaceobject_serializer_class = SpaceObjectSerializer
    spacecraft_model_class = UncrewedSpacecraft
    spacecraft_serializer_class = SpacecraftSerializer

    # Услуги_1.GET_список_с_id
    @extend_schema(
        summary="Получение информации о космических объектах",
        description="Список всех космических объектов.",
        responses={
            200: OpenApiResponse(response=UserSerializer(many=True),
                                 description="Список всех космических объектов")
        }
    )
    @method_permission_classes((AllowAny,))
    def get(self, request, format=None):
        query_search = self.request.query_params.get('object_search', None)
        draft_request = self.spacecraft_model_class.objects.filter(
            status='draft').first()
        spacecraft_serializer = self.spacecraft_serializer_class(
            draft_request, many=False)
        space_objects = self.spaceobject_model_class.objects.filter(
            is_active=True)
        if query_search:
            space_objects = space_objects.filter(name=query_search)
        serializer = self.spaceobject_serializer_class(space_objects,
                                                       many=True)
        return Response(
            {
                'spacecraft id': spacecraft_serializer.data.get(
                    'id') if draft_request else None,
                'space objects in spacecraft': spacecraft_serializer.data.get(
                    'space_object_count'),
                'space objects': serializer.data
            }, status=status.HTTP_200_OK
        )

    # Услуги_3.POST_добавление
    @extend_schema(
        summary="Добавление космического объекта",
        description="Добавляет новый космический объект.",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer,
                                 description="Объект успешно создан"),
            400: OpenApiResponse(description="Ошибка валидации")
        }
    )
    @method_permission_classes((IsAdmin, IsManager,))
    def post(self, request, format=None):
        serializer = self.spaceobject_serializer_class(data=request.data)
        if serializer.is_valid():
            # user = authenticate_user()
            user = request.user
            # creator_user = request.user
            new_spaceobject = serializer.save()
            # user1 = request.user
            SpaceObject.user = user
            serializer.save()
            pic1 = request.FILES.get('pic1')
            adding_pic_result = add_image(new_spaceobject, pic1, 'images')
            if 'error' in adding_pic_result.data:
                return adding_pic_result

            pic2 = request.FILES.get('pic2')
            adding_pic2_result = add_image(new_spaceobject, pic2, 'setImg')
            if 'error' in adding_pic2_result.data:
                return adding_pic2_result

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpaceObjectDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]

    model_class = SpaceObject
    serializer_class = SpaceObjectSerializer

    # Услуги_2.GET_одна_запись
    @extend_schema(
        summary="Получение информации о космическом объекте",
        description="Возвращает информацию о космическом объекте по его id.",
        responses={
            200: OpenApiResponse(response=UserSerializer(many=True),
                                 description="Информация об объекте")
        }
    )
    @method_permission_classes((IsAuthenticated,))
    def get(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(space_object)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # Услуги_4.PUT_изменение
    @extend_schema(
        summary="Изменение данных космического объекта.",
        description="Изменение данных космического объекта по его ID. "
                    "Если объект не найден, возвращает ошибку.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(description="Данные успешно изменены."),
            400: OpenApiResponse(description="ID объекта не предоставлен")
        }
    )
    @method_permission_classes((IsAdmin, IsManager,))
    def put(self, request, pk, format=None):
        # user = authenticate_user()
        user = request.user

        space_object = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(space_object, data=request.data,
                                           partial=True)
        if 'pic1' in serializer.initial_data:
            pic1_result = add_image(space_object,
                                    serializer.initial_data['pic1'], 'images')
            if 'error' in pic1_result.data:
                return pic1_result
        if 'pic2' in serializer.initial_data:
            pic2_result = add_image(space_object,
                                    serializer.initial_data['pic2'], 'setImg')
            if 'error' in pic2_result.data:
                return pic2_result

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Услуги_5.DELETE_удаление + изображение
    @extend_schema(
        summary="Удаление космического объекта.",
        description="Удаляет объект по его ID. "
                    "Если объект не найден, возвращает ошибку.",
        responses={
            204: OpenApiResponse(description="Объект успешно удалён"),
        }
    )
    @method_permission_classes((IsAdmin, IsManager,))
    def delete(self, request, pk, format=None):
        # user = authenticate_user()
        user = request.user

        space_object = get_object_or_404(self.model_class, pk=pk)
        if space_object.image_url:
            result = delete_image(space_object)
            if 'error' in result.data:
                return result
        space_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Услуги_6.POST добавления в заявку-черновик
    @extend_schema(
        summary="Добавление космического объекта в заявку-черновик",
        description="Добавляет космический объект в АМС-черновик.",
        # request=UserSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer,
                                 description="Объект успешно добавленн"),
            400: OpenApiResponse(
                description="Объект уже находится в заявке-черновике")
        }
    )
    @method_permission_classes((IsAuthenticated,))
    def post(self, request, pk, format=None):
        # user = authenticate_user()
        user = request.user
        space_object = get_object_or_404(SpaceObject, pk=pk)
        # user_creator = user

        draft_request = UncrewedSpacecraft.objects.filter(
            creator=user, status='draft').first()

        if draft_request:
            # 1. Заявка-черновик существует
            flight_space_object = FlightSpaceObject.objects.filter(
                spacecraft=draft_request, space_object=space_object).first()

            if not flight_space_object:
                # Связь не существует, создаем ее
                FlightSpaceObject.objects.create(
                    # spacecraft=draft_request,
                    space_object=space_object,
                    create_date=date.today()
                )
                return Response(
                    {'message': 'Объект успешно добавлен в заявку-черновик'},
                    status=status.HTTP_201_CREATED
                )
            else:
                # Связь уже существует
                return Response(
                    {'message': 'Объект уже находится в заявке-черновике'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # 2. Заявка-черновик не существует, создаем ее
            draft_request = UncrewedSpacecraft.objects.create(
                creator=user,
                status='draft',
                created_at=date.today()
            )
            FlightSpaceObject.objects.create(
                spacecraft=draft_request,
                space_object=space_object,
                create_date=date.today()
            )
            return Response(
                {'message': 'Заявка-черновик создана, объект добавлен'},
                status=status.HTTP_201_CREATED
            )


class SpacecraftList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    # ЗАЯВКИ_1.GET список
    @extend_schema(
        summary="Получение информации обо всех АМС",
        description="Возвращает список всех автоматических межпланетных станций.",
        responses={
            200: OpenApiResponse(response=UserSerializer(many=True),
                                 description="Список всех АМС")
        }
    )
    @method_permission_classes((IsAuthenticated,))
    def get(self, request, format=None):
        # user = authenticate_user()
        user = request.user
        # check_moderator(user)
        spacecrafts = (UncrewedSpacecraft.objects.filter(
            status__in=['draft', 'completed', 'formed', 'rejected'],
        )
            # .filter(
            #     Q(creator=user) | Q(moderator=user)
            # )
        )
        serializer = SpacecraftSerializerForList(spacecrafts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpacecraftDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]

    # ЗАЯВКИ_2.GET одна запись
    @extend_schema(
        summary="Получение информации об АМС",
        description="Возвращает информацию о АМС по его ID.",
        responses={
            200: OpenApiResponse(response=UserSerializer(many=True),
                                 description="Информация о АМС")
        }
    )
    @method_permission_classes((IsAdmin, IsManager, IsCreator,))
    def get(self, request, pk, format=None):
        # user = authenticate_user()
        user = request.user

        # spacecraft = get_object_or_404(
        #     UncrewedSpacecraft.objects.filter(status='draft').filter(
        #         Q(creator=user) | Q(moderator=user)), pk=pk)
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.filter(status='draft'), pk=pk)
        serializer = SpacecraftSerializer(spacecraft)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ЗАЯВКИ_3.PUT изменение доп. полей заявки
    @extend_schema(
        summary="Изменение данных АМС",
        description="Изменение АМС по его ID. Если АМС не найден, возвращает ошибку.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(description="Данные успешно изменены."),
            400: OpenApiResponse(description="ID АМС не проходит ваоидацию")
        }
    )
    @method_permission_classes((IsAdmin, IsManager, IsCreator,))
    def put(self, request, pk, format=None):
        # user = authenticate_user()
        user = request.user

        # user1 = request.user
        # check_moderator(user)
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.exclude(status='deleted').filter(
                Q(creator=user)), pk=pk)

        serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                          partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    # ЗАЯВКИ_6.DELETE_удаление
    @extend_schema(
        summary="Удаление АМС",
        description="Удаляет АМС по его ID. Если АМС не найден, возвращает ошибку.",
        responses={
            204: OpenApiResponse(description="АМС успешно удалён"),
            404: OpenApiResponse(description="АМС не найден"),
            400: OpenApiResponse(description="ID АМС не предоставлен")
        }
    )
    @method_permission_classes((IsAdmin, IsManager, IsCreator,))
    def delete(self, request, pk, format=None):
        # user = authenticate_user()
        user = request.user

        # user1 = request.user
        # check_moderator(user)
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.filter(status='draft').filter(
                Q(creator=user) | Q(moderator=user)), pk=pk)
        spacecraft.status = 'deleted'
        spacecraft.save(update_fields=['status'])  # Save only the status field

        return Response({"detail": "Удалено."},
                        status=status.HTTP_204_NO_CONTENT)


class FlightObject(APIView):  # m-m
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAdmin|IsManager]

    # M-M_1.DELETE удаление из заявки (без PK м-м)
    @extend_schema(
        summary="Удаление объект из АМС",
        description="Удаляет объект из АМС по его ID. Если объект не найден, возвращает ошибку.",
        responses={
            204: OpenApiResponse(description="Пользователь успешно удалён"),
            404: OpenApiResponse(description="Пользователь не найден"),
            400: OpenApiResponse(description="ID пользователя не предоставлен")
        }
    )
    def delete(self, request, pk_spacecraft, pk_space_object,
               format=None):
        # user = authenticate_user()
        user = request.user

        # user1 = request.user
        flight_object = get_object_or_404(FlightSpaceObject,
                                          spacecraft_id=pk_spacecraft,
                                          space_object_id=pk_space_object)
        flight_object.delete()
        # flight_object_list = FlightSpaceObject.objects.filter(object_pk=pk_space_objects)
        # return Response(FlightSpaceObjectSerializer(flight_object_list, many=True).data)
        return Response({"detail": "Удалено."},
                        status=status.HTTP_204_NO_CONTENT)

    # M-M_2.PUT изменение значения в м-м (без PK м-м)
    @extend_schema(
        summary="Изменение значения в полёте АМС к объекту",
        description="Изменение данных в полёте АМС к объекту по его ID. "
                    "Если пользователь не найден, возвращает ошибку.",
        request=UserSerializer,
        responses={
            200: OpenApiResponse(description="Данные успешно изменены."),
            403: OpenApiResponse(
                description="Недостаточно прав для изменений"),
            404: OpenApiResponse(description="Пользователь не найден"),
            400: OpenApiResponse(description="ID пользователя не предоставлен")
        }
    )
    # @method_permission_classes((IsAdmin,))
    def put(self, request, pk_spacecraft, pk_space_object,
            format=None):
        # user = authenticate_user()
        user = request.user
        flight_object = get_object_or_404(FlightSpaceObject,
                                          spacecraft_id=pk_spacecraft,
                                          space_object_id=pk_space_object)
        serializer = FlightSpaceObjectSerializer(flight_object,
                                                 data=request.data,
                                                 partial=True)
        if serializer.is_valid():
            # Автоматическое заполнение поля SpaceObject.name
            space_object_name = serializer.validated_data.get(
                'space_object', {}).get('name')
            if space_object_name:
                space_object = flight_object.space_object
                space_object.name = space_object_name
                space_object.save()

            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ЗАЯВКИ_7.POST добавление изображения (MINIO)
@extend_schema(
    summary="Добавление изображения",
    description="Добавление изображения по id услуги, старое изображение "
                "заменяется/удаляется",
    request=UserSerializer,
    responses={
        200: OpenApiResponse(response=UserSerializer,
                             description="Изображение добавлено/изменено."),
        400: OpenApiResponse(description="Ошибки валидации")
    }
)
@api_view(['POST'])
@permission_classes([IsAdmin|IsManager])
@authentication_classes([IsAuthenticated])
def add_image(request, pk, format=None):
    space_object = get_object_or_404(SpaceObject, pk=pk)
    pic1 = request.FILES.get('pic1')
    result = add_image(space_object, pic1, 'images')
    if 'error' in result.data:
        return result
    pic2 = request.FILES.get('pic2')
    result = add_image(SpaceObject, pic2, 'setImg')
    if 'error' in result.data:
        return result

    return Response(status=status.HTTP_200_OK)


# ЗАЯВКИ_4.PUT сформировать создателем
@extend_schema(
    summary="Формирование АМС создателем, дата формирования",
    description="Изменение данных по его ID. Если АМС не найден, возвращает ошибку.",
    request=UserSerializer,
    responses={
        200: OpenApiResponse(description="Данные успешно изменены."),
        403: OpenApiResponse(description="Недостаточно прав для изменений"),
        404: OpenApiResponse(description="Пользователь не найден"),
        400: OpenApiResponse(description="ID пользователя не предоставлен")
    }
)
@api_view(['PUT'])
# @permission_classes([IsAdmin | IsManager])
@permission_classes([IsAdmin|IsManager|IsCreator])
@authentication_classes([SessionAuthentication])
def save_spacecraft(request, pk, format=None):
    # user = authenticate_user()
    user = request.user

    # spacecraft = get_object_or_404(
    #     UncrewedSpacecraft.objects.exclude(status='deleted').filter(
    #         Q(creator=user) | Q(moderator=user)), pk=pk)
    spacecraft = get_object_or_404(
        UncrewedSpacecraft.objects.exclude(status='deleted'), pk=pk)
    if user == spacecraft.creator:
        if request.data.get(spacecraft.status == 'draft'):
            if not spacecraft.spacecraft_name and not request.data.get(
                    'spacecraft_name'):
                raise ValidationError(
                    {'spacecraft_name': 'Обязательное поле.'}
                )
            if not spacecraft.scheduled_at and not request.data.get(
                    'scheduled_at'):
                raise ValidationError(
                    {'scheduled_at': 'Обязательное поле.'})
            spacecraft.status = 'formed'
            spacecraft.formed_at = timezone.now()

        elif request.data.get('status') in ('completed', 'rejected'):
            raise ValidationError(
                {
                    'status': 'Создатель не может изменить статус на completed или rejected'})
    else:
        raise ValidationError(
            {'error': 'У вас нет прав для изменения этой заявки'})

    serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                      partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)


# ЗАЯВКИ_5.PUT завершить/отклонить модератором
@extend_schema(
    summary="Изменение данных. Завершить/отклонить модератором",
    description="Изменение данных по ID. Если АМС не найден, возвращает ошибку.",
    request=UserSerializer,
    responses={
        200: OpenApiResponse(description="Данные успешно изменены."),
        403: OpenApiResponse(description="Недостаточно прав для изменений"),
        404: OpenApiResponse(description="Пользователь не найден"),
        400: OpenApiResponse(description="ID пользователя не предоставлен")
    }
)
@api_view(['PUT'])
@permission_classes([IsAdmin|IsManager])
@authentication_classes([SessionAuthentication])
def moderate_spacecraft(request, pk, format=None):
    # user = authenticate_user()
    user = request.user
    # user1 = request.user
    spacecraft = get_object_or_404(
        UncrewedSpacecraft.objects.exclude(status='deleted'), pk=pk)
    # if user == spacecraft.moderator:
    if request.data.get('status') in ('completed', 'rejected'):
        spacecraft.status = request.data.get('status')
        spacecraft.moderator = user
        spacecraft.completed_at = timezone.now()

        for space_obj in spacecraft.space_objects.all():
            space_obj.is_priority = True
            space_obj.save()
    else:
        raise ValidationError(
            {
                'status': 'Модератор может изменить статус только на completed или rejected'})

    #else:
    #    raise ValidationError(
    #        {'error': 'У вас нет прав для изменения этой заявки'})

    serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                      partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)


class UserRegistration(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Регистрация пользователя",
        description="Создаёт нового пользователя с уникальным email, именем, фамилией.",
        request=UserSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer,
                                 description="Пользователь успешно создан"),
            400: OpenApiResponse(description="Ошибки валидации")
        }
    )
    # @method_permission_classes((AllowAny,))
    def post(self, request):
        # Удаляем поля is_superuser и is_staff из данных запроса, если они есть
        request_data = request.data.copy()
        request_data.pop('is_superuser', None)
        request_data.pop('is_staff', None)

        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()  # Сохраняем пользователя через сериализатор

            return Response(
                {'status': 'Created', 'user_id': user.id},
                status=status.HTTP_201_CREATED
            )

        return Response({'status': 'Error', 'error': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


class UserPut(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    model = get_user_model()
    serializer_class = UserSerializer

    @extend_schema(
        summary="Изменение данных пользователя",
        description="Изменение данных по его ID. Если пользователь не найден, возвращает ошибку.",
        request=UserSerializer,
        responses={
            202: OpenApiResponse(description="Данные успешно изменены."),
            403: OpenApiResponse(
                description="Недостаточно прав для изменений"),
            404: OpenApiResponse(description="Пользователь не найден"),
            400: OpenApiResponse(description="ID пользователя не предоставлен")
        }
    )
    @method_permission_classes((IsAdmin,IsManager))
    def put(self, request, pk, format=None):
        try:
            user = AuthUser.objects.get(pk=pk)
        except AuthUser.DoesNotExist:
            return Response({"error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)

        # Проверяем, является ли текущий пользователь администратором
        if not request.user.is_superuser or not request.user.is_staff:
            # Если текущий пользователь не администратор, запрещаем изменение полей is_superuser и is_staff
            if 'is_superuser' in request.data or 'is_staff' in request.data:
                return Response(
                    {'status': 'Error',
                     'error': 'You do not have permission to change user roles.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.serializer_class(user, data=request.data,
                                           partial=True)

        if serializer.is_valid():
            user = serializer.save()
            if 'password' in serializer.validated_data:
                user.set_password(serializer.validated_data.get('password'))
                user.save()
            return Response(
                {'status': 'Updated', 'user_id': user.id},
                status=status.HTTP_202_ACCEPTED
            )

        return Response({'status': 'Error', 'error': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)


# @method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Авторизация пользователя",
        description="Авторизация по email и паролю.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(response=UserSerializer,
                                 description="Авторизация успешна"),
            404: OpenApiResponse(description="Провалена")
        }
    )
    # @method_decorator(csrf_exempt)
    def post(self, request, format=None):  # аутентификация
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {'status': 'error', 'error': 'Email и пароль обязательны.'},
                status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)
        # user = request.user
        if user is not None:
            login(request, user)

            random_key = str(uuid.uuid4())
            session_storage.set(random_key, email)

            old_ssid = request.COOKIES.get('session_id', '')
            if old_ssid:
                if session_storage.get(old_ssid):
                    session_storage.delete(old_ssid)

            response = Response({'status': 'ok'}, status=status.HTTP_200_OK)
            response.set_cookie("session_id", random_key)
            login(request, user)

            return response
        else:
            return Response({'status': 'error', 'error': 'login failed'},
                            status=status.HTTP_401_UNAUTHORIZED)


# class UserTest(APIView):
#     def get(self, request):
#         user = self.request.user
#         # print(f"user (UserTest.post): {user}")
#         return Response(
#             {'status': 'Get', 'user_id': user.id},
#             status=status.HTTP_200_OK
#         )


class LogoutView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Выход из системы",
        description="Прекращение сессии.",
        responses={
            204: OpenApiResponse(response=UserSerializer,
                                 description="Сеанс завершен."),
            403: OpenApiResponse(description="Ошибка. Сеанс не завершен.")
        }
    )
    @csrf_exempt
    # @method_decorator(csrf_exempt)
    # @method_permission_classes((IsAuthenticated,))
    def post(self, request, format=None):
        user = request.user
        # # user = authenticate_user(request)
        # print(f"user (LogoutView.post): {user.email}")
        # if not user or not user.is_authenticated:
        #     return Response({'error': 'User not authenticated'}, status=401)
        # # if user.is_authenticated:
        logout(request._request)

        ssid = request.COOKIES.get("session_id")
        if ssid:
            session_storage.delete(ssid)

        # Clear the session cookie
        response = Response({'status': 'Success'},
                            status=status.HTTP_204_NO_CONTENT)
        # response.delete_cookie("session_id")

        return response


class UserList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    # permission_classes = [IsAuthenticated]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Получение информации обо всех пользователях",
        description="Возвращает список всех зарегистрированных пользователей.",
        responses={
            200: OpenApiResponse(response=UserSerializer(many=True),
                                 description="Список всех пользователей")
        }
    )
    def get(self, request):
        users = AuthUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)


class UserDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    http_method_names = ['get']

    # permission_classes = [IsAdmin | IsManager]
    @extend_schema(
        summary="Получение информации о пользователе",
        description="Возвращает информацию о пользователе по его ID.",
        responses={
            200: OpenApiResponse(response=UserSerializer,
                                 description="Информация о пользователе"),
            404: OpenApiResponse(description="Пользователь не найден")
        }
    )
    def get(self, request, user_id):
        try:
            user = AuthUser.objects.get(id=user_id)
        except AuthUser.DoesNotExist:
            return Response({"error": "User not found"},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserDelete(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Удаление пользователя",
        description="Удаляет пользователя по его ID. Если пользователь не найден, возвращает ошибку.",
        responses={
            204: OpenApiResponse(description="Пользователь успешно удалён"),
            404: OpenApiResponse(description="Пользователь не найден"),
            400: OpenApiResponse(description="ID пользователя не предоставлен")
        }
    )
    def delete(self, request, user_id):
        if user_id:
            try:
                user = AuthUser.objects.get(id=user_id)
                user.delete()
                return Response({"status": "User deleted"},
                                status=status.HTTP_204_NO_CONTENT)
            except AuthUser.DoesNotExist:
                return Response({"error": "User not found"},
                                status=status.HTTP_404_NOT_FOUND)
        return Response({"error": "User ID not provided"},
                        status=status.HTTP_400_BAD_REQUEST)


# class SomeView(APIView):
#     permission_classes = [IsAuthenticatedUser]
#
#     def get(self, request, format=None):
#         if isinstance(request.user, AnonymousUser):
#             return Response({'status': 'error',
#                              'error': 'Пользователь не аутентифицирован.'},
#                             status=status.HTTP_401_UNAUTHORIZED)
#
#         # Если пользователь аутентифицирован, вы можете использовать request.user
#         return Response({'status': 'success', 'user': str(request.user)},
#                         status=status.HTTP_200_OK)
