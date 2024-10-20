from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
#from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import api_view, permission_classes

from lab.views import spacecraft
from .minio import *
from lab.models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject, \
    AuthUser
from api.serializers import (SpaceObjectSerializer,
                             SpacecraftSerializer,
                             UserSerializer, UserUpdateSerializer,
                             FlightSpaceObjectSerializer, SpacecraftSerializerForList)
from datetime import date


class UsersList(APIView):
    model_class = AuthUser
    serializer_class = UserSerializer

    def get(self, request, format=None):
        user = self.model_class.objects.all()
        serializer = self.serializer_class(user, many=True)
        return Response(serializer.data)


def user():
    defaults = {'email': 'api@api.com',
                'password': '222'}  # Set a strong password
    api_user, created = AuthUser.objects.get_or_create(username='api_user',
                                                       defaults=defaults)
    return api_user


class SpaceObjectList(APIView):
    spaceobject_model_class = SpaceObject
    spaceobject_serializer_class = SpaceObjectSerializer
    spacecraft_model_class = UncrewedSpacecraft
    spacecraft_serializer_class = SpacecraftSerializer

    # Услуги_1.GET_список_с_id
    def get(self, request, format=None):
        query_search = self.request.query_params.get('object_search', None)
        draft_request = self.spacecraft_model_class.objects.filter(
            # user=request.user,
            # user=get_current_user(),
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
                'space objects in spacecraft': spacecraft_serializer.data.get(
                    'space_object_count'),
                'space objects': serializer.data
            }
        )

    # Услуги_3.POST_добавление
    def post(self, request, format=None):
        serializer = self.spaceobject_serializer_class(data=request.data)
        if serializer.is_valid():
            # Указываем создателя заявки как синглтон
            # creator_user = get_api_user()
            new_spaceobject = serializer.save()
            user1 = user()
            SpaceObject.user = user1
            serializer.save()
            #pic1 = request.FILES.get('pic1')
            #adding_pic_result = add_image(new_spaceobject, pic1, 'images')
            #if 'error' in adding_pic_result.data:
            #    return adding_pic_result

            #pic2 = request.FILES.get('pic2')
            #adding_pic2_result = add_image(new_spaceobject, pic2, 'setImg')
            #if 'error' in adding_pic2_result.data:
            #    return adding_pic2_result

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SpaceObjectDetail(APIView):
    model_class = SpaceObject
    serializer_class = SpaceObjectSerializer

    # Услуги_2.GET_одна_запись
    def get(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(space_object)
        return Response(serializer.data)

    # Услуги_4.PUT_изменение
    def put(self, request, pk, format=None):
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
    def delete(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        if space_object.image_url:
            result = delete_image(space_object)
            if 'error' in result.data:
                return result
        space_object.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    # Услуги_6.POST добавления в заявку-черновик
    def post(self, request, pk, format=None):
        space_object = get_object_or_404(SpaceObject, pk=pk)
        user_creator = user()  # Предполагается, что user() возвращает текущего пользователя API

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
                #creator=user_creator,
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
    # permission_classes = [IsAuthenticated]
    #permission_classes = [AllowAny]

    # ЗАЯВКИ_1.GET список
    def get(self, request, format=None):
        # Получаем текущего пользователя
        user1 = user()

        # Фильтруем объекты UncrewedSpacecraft по статусу и проверяем модератора и создателя
        spacecrafts = UncrewedSpacecraft.objects.filter(
            status__in=['completed', 'formed', 'rejected'],
            # Исключаем 'deleted' и 'draft'
        ).filter(
            Q(creator=user1) | Q(moderator=user1)
            # Проверяем, является ли пользователь создателем или модератором
        )
        #serializer = SpacecraftSerializer(spacecrafts, many=True)
        serializer = SpacecraftSerializerForList(spacecrafts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # def post(self, request, *args, **kwargs):
    #     creator_user = request.user  # Создатель заявки — текущий пользователь
    #     request.data['creator'] = creator_user.id
    #     return self.create(request, *args, **kwargs)


class SpacecraftDetail(APIView):
    #permission_classes = [IsAuthenticated]

    # ЗАЯВКИ_2.GET одна запись
    def get(self, request, pk, format=None):
        user1 = user()
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.filter(status='draft').filter(
                Q(creator=user1) | Q(moderator=user1)), pk=pk)
        serializer = SpacecraftSerializer(spacecraft)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ЗАЯВКИ_3.PUT изменение доп. полей заявки
    def put(self, request, pk, format=None):
        # user = get_api_user()
        user1 = user()
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.exclude(status='deleted').filter(
                Q(creator=user1) | Q(moderator=user1)), pk=pk)

        serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                          partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)

    # ЗАЯВКИ_6.DELETE_удаление
    def delete(self, request, pk, format=None):
        user1 = user()
        spacecraft = get_object_or_404(
            UncrewedSpacecraft.objects.filter(status='draft').filter(
                Q(creator=user1) | Q(moderator=user1)), pk=pk)
        spacecraft.status = 'deleted'
        spacecraft.save(update_fields=['status'])  # Save only the status field

        return Response({"detail": "Удалено."},
                        status=status.HTTP_204_NO_CONTENT)


class FlightObject(APIView):  # m-m
    #permission_classes = [IsAuthenticated]

    # M-M_1.DELETE удаление из заявки (без PK м-м)
    def delete(self, request, pk_spacecraft, pk_space_object,
               format=None):
        user1 = user()
        if user1 == UncrewedSpacecraft.moderator or AuthUser.is_superuser or AuthUser.is_staff:
            flight_object = get_object_or_404(
                FlightSpaceObject,
                spacecraft_id=pk_spacecraft,
                space_object_id=pk_space_object)
            flight_object.delete()
            # flight_object_list = FlightSpaceObject.objects.filter(object_pk=pk_space_objects)
            # return Response(FlightSpaceObjectSerializer(flight_object_list, many=True).data)
            return Response({"detail": "Удалено."},
                            status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'message': 'У вас недостаточно прав'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # M-M_2.PUT изменение количества/порядка/значения в м-м (без PK м-м)

    def put(self, request, pk_spacecraft, pk_space_object, format=None):
        try:
            # Получаем объект FlightSpaceObject по переданным параметрам
            flight_space_object = FlightSpaceObject.objects.get(
                spacecraft_id=pk_spacecraft,
                space_object_id=pk_space_object
            )
        except FlightSpaceObject.DoesNotExist:
            return Response({"error": "Объект полета не найден."}, status=status.HTTP_404_NOT_FOUND)

        # Извлекаем значение is_priority из запроса
        is_priority = request.data.get('is_priority', None)

        if is_priority is not None:
            # Обновляем поле is_priority
            flight_space_object.is_priority = is_priority
            flight_space_object.save()

            # Сериализуем обновленный объект для ответа
            serializer = FlightSpaceObjectSerializer(flight_space_object)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Поле 'is_priority' не указано."}, status=status.HTTP_400_BAD_REQUEST)


    #     def put(self, request, pk_spacecraft, pk_space_object,
    #             format=None):
    #         user1 = user()
    #         if user1 == UncrewedSpacecraft.moderator or AuthUser.is_superuser or AuthUser.is_staff:
    #             flight_object = get_object_or_404(
    #                 FlightSpaceObject,
    #                 spacecraft_id=pk_spacecraft,
    #                 space_object_id=pk_space_object)
    #             serializer = FlightSpaceObjectSerializer(flight_object,
    #                                                      data=request.data,
    #                                                      partial=True)
    #             if serializer.is_valid():
    #                 # Автоматическое заполнение поля SpaceObject.name
    #                 space_object_name = serializer.validated_data.get(
    #                     'space_object', {}).get('name')
    #                 if space_object_name:
    #                     space_object = flight_object.space_object
    #                     space_object.name = space_object_name
    #                     space_object.save()
    #
    #                 serializer.save()
    #                 return Response(serializer.data)
    #             return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #         else:
    #             return Response(
    #                 {'message': 'У вас недостаточно прав'},
    #                 status=status.HTTP_400_BAD_REQUEST
    #             )


# ЗАЯВКИ_7.POST добавление изображения
@api_view(['POST'])
def add_image(request, pk, format=None):
    spaceobject = get_object_or_404(SpaceObject, pk=pk)
    pic = request.FILES.get('pic')
    result = add_pic(spaceobject, pic, 'images') #
    if 'error' in result.data:
        return result
    #pic2 = request.FILES.get('pic2')
    #result = add_pic(spaceobject, pic2, 'setImg')
    #if 'error' in result.data:
    #    return result

    return Response(status=status.HTTP_200_OK)



# ЗАЯВКИ_4.PUT сформировать создателем
@api_view(['PUT'])
def save_spacecraft(request, pk, format=None):
    user1 = user()  # Предполагается, что эта функция возвращает текущего пользователя
    spacecraft = get_object_or_404(
        UncrewedSpacecraft.objects.exclude(status='deleted').filter(
            Q(creator=user1) | Q(moderator=user1)), pk=pk
    )

    if user1 == spacecraft.creator:
        # Проверяем, если статус 'draft'
        if spacecraft.status == 'draft':
            # Проверяем обязательные поля
            if not request.data.get('spacecraft_name'):
                raise ValidationError({'spacecraft_name': 'Обязательное поле.'})
            if not request.data.get('scheduled_at'):
                raise ValidationError({'scheduled_at': 'Обязательное поле.'})

            # Обновляем статус и дату формирования
            spacecraft.status = 'formed'
            spacecraft.formed_at = timezone.now()

        elif request.data.get('status') in ('completed', 'rejected'):
            raise ValidationError({
                'status': 'Создатель не может изменить статус на completed или rejected'
            })

    else:
        return Response(
            {'message': 'У вас недостаточно прав'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Обновляем поля spacecraft на основе данных запроса
    serializer = SpacecraftSerializer(spacecraft, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()  # Сохраняем изменения
        return Response(serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ЗАЯВКИ_5.PUT завершить/отклонить модератором
@api_view(['PUT'])
def moderate_spacecraft(request, pk, format=None):
    # user = get_api_user()
    user1 = user()
    spacecraft = get_object_or_404(
        UncrewedSpacecraft.objects.exclude(status='deleted').filter(
            Q(creator=user1) ), pk=pk) #| Q(moderator=user1)
    if user1 == spacecraft.moderator: # ! сам себя может прописать модером !
        if request.data.get('status') in ('completed', 'rejected'):
            spacecraft.status = request.data.get('status')
            spacecraft.moderator = user1
            spacecraft.completed_at = timezone.now()

            for space_obj in spacecraft.space_objects.all():
                space_obj.is_priority = True
                space_obj.save()
        else:
            raise ValidationError(
                {
                    'status': 'Модератор может изменить статус только на completed или rejected'})

    else:
        return Response(
            {'message': 'У вас недостаточно прав'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = SpacecraftSerializer(spacecraft, data=request.data,
                                      partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user1 = serializer.save()
#        token = Token.objects.create(user=user1)
        return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user1 = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user1)
     #   token, created = Token.objects.get_or_create(user=user1)
     #   return Response({'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Неверные учетные данные'},
                    status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout_view(request):
   # request.user.auth_token.delete()
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['PUT'])
#@permission_classes([IsAuthenticated])
def update_user(request):
    user1 = user()
    serializer = UserUpdateSerializer(user1, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
