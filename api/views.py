from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.authentication import SessionAuthentication, \
    BasicAuthentication
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, \
    IsAuthenticated
from rest_framework.decorators import api_view, permission_classes, \
    authentication_classes
from lab.models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject, \
    AuthUser
from api.serializers import (SpaceObjectSerializer,
                             SpacecraftSerializer,
                             UserSerializer,
                             UserUpdateSerializer,
                             FlightSpaceObjectSerializer)
from .permissions import IsAdmin, IsManager #, IsAuthenticatedUser, IsAnyUser
from .minio import *

from datetime import date
from drf_yasg.utils import swagger_auto_schema

from django.conf import settings
import redis
import uuid


# Connect to our Redis instance
User = get_user_model()
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


def check_moderator(user):
    if user.is_superuser or user.is_staff:
        UncrewedSpacecraft.objects.filter(
            moderator__isnull=True).update(moderator=user)


class UserViewSet(viewsets.ModelViewSet):
    #authentication_classes = [SessionAuthentication, BasicAuthentication]
    #http_method_names = ['post', 'put', 'get'] #

    model_class = AuthUser
    serializer_class = UserSerializer
    update_serializer_class = UserUpdateSerializer
    queryset = AuthUser.objects.all()

    """Метод GET user/ и user/<int:pk>"""
    #def get_permissions(self):
    #     if self.action == 'list':
    #         return [IsAuthenticated()]
    #     elif self.action == 'retrieve':
    #         return [IsAuthenticated()]
    #     return super().get_permissions()

    #def is_moderator(self, user):
    #    return UncrewedSpacecraft.objects.filter(moderator=user).exists()

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def method_permission_classes(classes):
        def decorator(func):
            def decorated_func(self, *args, **kwargs):
                self.permission_classes = classes
                self.check_permissions(self.request)
                return func(self, *args, **kwargs)

            return decorated_func

        return decorator

    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    @method_permission_classes((IsAdmin)) # IsAuthenticatedUser,
    def list(self, request, *args, **kwargs):
         if not (
                 request.user.is_superuser or request.user.is_staff or self.is_moderator(
                 request.user)):
             raise PermissionDenied(
                 "У вас нет прав для просмотра списка пользователей.")

         queryset = self.get_queryset()
         serializer = self.get_serializer(queryset, many=True)
         return Response(serializer.data)

    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    @method_permission_classes((IsAdmin)) # IsAuthenticatedUser,
    def retrieve(self, request, *args, **kwargs):
         instance = self.get_object()
         if request.user != instance and not (
                 request.user.is_superuser or request.user.is_staff):
             raise PermissionDenied(
                 "У вас нет прав для просмотра данных этого пользователя.")

         serializer = self.get_serializer(instance)
         return Response(serializer.data)


    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    @method_permission_classes((IsManager)) # IsAuthenticatedUser,
    def create(self, request):
        if self.model_class.objects.filter(
                username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user1 = serializer.save()  # Сохраняем пользователя

            # # Теперь используем validated_data для доступа к данным
            # if user1.is_superuser or user1.is_staff:
            #     spacecrafts_without_moderator = UncrewedSpacecraft.objects.filter(
            #         Q(moderator__isnull=True)
            #     )
            #     spacecrafts_without_moderator.update(moderator=user1)
             
            # Теперь можно безопасно получить данные пользователя
            return Response(
                {'status': 'Created', 'user_id': user1.id},
                status=201
            )

        return Response({'status': 'Error', 'error': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    @method_permission_classes((IsAdmin,)) #IsAuthenticatedUser,
    def update(self, request, pk=None):
        try:
            user1 = self.get_object()  # Получаем пользователя по pk
        except AuthUser.DoesNotExist:
            return Response({'status': 'Not Found'}, status=404)

        serializer = self.update_serializer_class(user1, data=request.data,
                                                  partial=True)
        if serializer.is_valid():
            serializer.save()
            if 'is_superuser' in serializer.validated_data or 'is_staff' in serializer.validated_data:
                if user1.is_superuser or user1.is_staff:
                    spacecrafts_without_moderator = UncrewedSpacecraft.objects.filter(
                        Q(moderator__isnull=True)
                    )
                    spacecrafts_without_moderator.update(moderator=user1)
                else:
                    UncrewedSpacecraft.objects.filter(moderator=user1).update(
                        moderator=None)
            return Response({'status': 'Updated', 'user': serializer.data},
                            status=200)

        return Response({'status': 'Error', 'error': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    # def delete(self, request, pk=None):
    #     try:
    #         user = self.get_object()  # Получаем пользователя по pk
    #         user.delete()  # Удаляем пользователя
    #         return Response({'status': 'Deleted'},
    #                         status=204)  # Возвращаем статус 204 No Content
    #     except CustomUser.DoesNotExist:
    #         return Response({'status': 'Not Found'},
    #                         status=404)  # Если пользователь не найден, возвращаем 404


class SpaceObjectList(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    spaceobject_model_class = SpaceObject
    spaceobject_serializer_class = SpaceObjectSerializer
    spacecraft_model_class = UncrewedSpacecraft
    spacecraft_serializer_class = SpacecraftSerializer

    # Услуги_1.GET_список_с_id
    @method_permission_classes((IsManager,)) #IsAnyUser
    def get(self, request, format=None):
        query_search = self.request.query_params.get('object_search', None)
        draft_request = self.spacecraft_model_class.objects.filter(
            user=request.user,
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
                'spacecraft': spacecraft_serializer.data.get(
                    'id') if draft_request else None,
                'space objects': serializer.data
            }
        )

    # Услуги_3.POST_добавление
    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    @method_permission_classes((IsAdmin,)) # IsAuthenticatedUser
    def post(self, request, format=None):
        serializer = self.spaceobject_serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
            if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
                return user
            # creator_user = request.user
            new_spaceobject = serializer.save()
            #user1 = request.user
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
    permission_classes = [IsAuthenticatedOrReadOnly]

    model_class = SpaceObject
    serializer_class = SpaceObjectSerializer

    # Услуги_2.GET_одна_запись
    @method_permission_classes((IsManager,)) # IsAnyUser
    def get(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(space_object)
        return Response(serializer.data)

    # Услуги_4.PUT_изменение
    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    @method_permission_classes((IsAdmin,)) # IsAuthenticatedUser
    def put(self, request, pk, format=None):
        user = request.user #authenticate_user_by_session(request._request) #
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

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
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Услуги_5.DELETE_удаление + изображение
    @method_permission_classes((IsAdmin,)) # IsAuthenticatedUser
    def delete(self, request, pk, format=None):

        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

        space_object = get_object_or_404(self.model_class, pk=pk)
        if space_object.image_url:
            result = delete_image(space_object)
            if 'error' in result.data:
                return result
        space_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Услуги_6.POST добавления в заявку-черновик
    @method_permission_classes((IsManager,)) # IsAuthenticatedUser
    @swagger_auto_schema(request_body=SpaceObjectSerializer)
    def post(self, request, pk, format=None):
        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

        space_object = get_object_or_404(SpaceObject, pk=pk)
        user_creator = user

        draft_request = UncrewedSpacecraft.objects.filter(
            creator=user_creator, status='draft').first()

        if draft_request:
            # 1. Заявка-черновик существует
            flight_space_object = FlightSpaceObject.objects.filter(
                spacecraft=draft_request, space_object=space_object).first()

            if not flight_space_object:
                # Связь не существует, создаем ее
                FlightSpaceObject.objects.create(
                    spacecraft=draft_request,
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
                user=user_creator,
                creator=user_creator,
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
    permission_classes = [IsAuthenticated] #IsAuthenticatedUser

    @method_permission_classes((IsManager,IsAdmin,))
    # ЗАЯВКИ_1.GET список
    def get(self, request, format=None):
        #user = request.user #authenticate_user_by_session(request._request) =authenticate_user_by_session(request)
        #if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
        #     return user
        #user = get_user_id_from_session(self, request)
        user = request.user
        check_moderator(user)
        spacecrafts = UncrewedSpacecraft.objects.filter(
            status__in=['completed', 'formed', 'rejected', 'draft'],
        ).filter(
            Q(creator=user) | Q(moderator=user)
        )
        serializer = SpacecraftSerializer(spacecrafts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SpacecraftDetail(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated] #IsAuthenticatedUser

    # ЗАЯВКИ_2.GET одна запись
    @method_permission_classes((IsManager,IsAdmin,))
    def get(self, request, pk, format=None):
        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

        # user1 = request.user
        check_moderator(user)
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.filter(status='draft').filter(
                Q(creator=user) | Q(moderator=user)), pk=pk)
        serializer = SpacecraftSerializer(spacecraft)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ЗАЯВКИ_3.PUT изменение доп. полей заявки
    @method_permission_classes((IsManager,IsAdmin,))
    @swagger_auto_schema(request_body=SpacecraftSerializer)
    def put(self, request, pk, format=None):
        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

        # user1 = request.user
        check_moderator(user)
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.exclude(status='deleted').filter(
                Q(creator=user) | Q(moderator=user)), pk=pk)

        serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                          partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    # ЗАЯВКИ_6.DELETE_удаление
    @method_permission_classes((IsAdmin,IsManager,))
    def delete(self, request, pk, format=None):
        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

        #user1 = request.user
        check_moderator(user)
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.filter(status='draft').filter(
                Q(creator=user) | Q(moderator=user)), pk=pk)
        spacecraft.status = 'deleted'
        spacecraft.save(update_fields=['status'])  # Save only the status field

        return Response({"detail": "Удалено."},
                        status=status.HTTP_204_NO_CONTENT)


class FlightObject(APIView):  # m-m
    authentication_classes = [SessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly] #IsAuthenticatedUser

    # M-M_1.DELETE удаление из заявки (без PK м-м)
    @method_permission_classes((IsAdmin,))
    def delete(self, request, pk_spacecraft, pk_space_object,
               format=None):
        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user

        #user1 = request.user
        flight_object = get_object_or_404(FlightSpaceObject,
                                          spacecraft_id=pk_spacecraft,
                                          space_object_id=pk_space_object)
        flight_object.delete()
        # flight_object_list = FlightSpaceObject.objects.filter(object_pk=pk_space_objects)
        # return Response(FlightSpaceObjectSerializer(flight_object_list, many=True).data)
        return Response({"detail": "Удалено."},
                        status=status.HTTP_204_NO_CONTENT)

    # M-M_2.PUT изменение количества/порядка/значения в м-м (без PK м-м)
    @swagger_auto_schema(request_body=FlightSpaceObjectSerializer)
    @method_permission_classes((IsAdmin,))
    def put(self, request, pk_spacecraft, pk_space_object,
            format=None):
        user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
        if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
            return user
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
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ЗАЯВКИ_7.POST добавление изображения
@swagger_auto_schema(method='post', request_body=SpaceObjectSerializer)
@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly] ) #IsAuthenticatedUser
@authentication_classes([])
def add_image(request, pk, format=None):
    planett = get_object_or_404(SpaceObject, pk=pk)
    pic1 = request.FILES.get('pic1')
    result = add_image(planett, pic1, 'images')
    if 'error' in result.data:
        return result
    pic2 = request.FILES.get('pic2')
    result = add_image(SpaceObject, pic2, 'setImg')
    if 'error' in result.data:
        return result

    return Response(status=status.HTTP_200_OK)


# ЗАЯВКИ_4.PUT сформировать создателем
@swagger_auto_schema(method='put', request_body=SpacecraftSerializer)
@api_view(['PUT'])
# @permission_classes([IsAdmin | IsManager])
@permission_classes([IsAuthenticatedOrReadOnly] ) #IsAuthenticatedUser
@authentication_classes([])
def save_spacecraft(request, pk, format=None):
    user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
    if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
        return user
    #user1 = request.user
    check_moderator(user)
    spacecraft = get_object_or_404(
        UncrewedSpacecraft.objects.exclude(status='deleted').filter(
            Q(creator=user) | Q(moderator=user)), pk=pk)
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
        return Response(serializer.data)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)


# ЗАЯВКИ_5.PUT завершить/отклонить модератором
@swagger_auto_schema(method='put', request_body=SpacecraftSerializer)
@api_view(['PUT'])
@permission_classes([IsAdmin | IsManager])
@authentication_classes([])
def moderate_spacecraft(request, pk, format=None):
    user = request.user #authenticate_user_by_session(request._request) #authenticate_user_by_session(request)
    if isinstance(user, Response):  # Проверяем, вернула ли функция ошибку
        return user
    #user1 = request.user
    spacecraft = get_object_or_404(
        UncrewedSpacecraft.objects.exclude(status='deleted'), pk=pk)
    if user == spacecraft.moderator:
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

    else:
        raise ValidationError(
            {'error': 'У вас нет прав для изменения этой заявки'})

    serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                      partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['POST'])
@permission_classes([AllowAny])
@authentication_classes([])
def login_view(request):
    username = request.data["username"]
    password = request.data["password"]
    user = authenticate(request, username=username, password=password)
    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")



@swagger_auto_schema(method='post')
@api_view(['POST'])
@permission_classes([IsAuthenticatedOrReadOnly] ) #IsAuthenticatedUser
def logout_view(request):
    if request.user.is_authenticated:
        logout(request)

        ssid = request.COOKIES.get("session_id")
        if ssid:
            session_storage.delete(ssid)

        # Clear the session cookie
        response = Response({'status': 'Success'},
                            status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie("session_id")

        return response

    return Response({'status': 'Error', 'error': 'User not authenticated'},
                    status=status.HTTP_401_UNAUTHORIZED)


# @swagger_auto_schema(method='put', request_body=UserUpdateSerializer)
# @api_view(['PUT'])
# @permission_classes([IsAuthenticatedUser])
# def update_user(request):
#     user = request.user
#     serializer = UserUpdateSerializer(user, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
