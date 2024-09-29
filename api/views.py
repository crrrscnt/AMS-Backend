from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from rest_framework import status
from api.serializers import (SpaceObjectSerializer,
                             SpaceObjectDetailSerializer,
                             UncrewedSpacecraftSerializer,
                             UncrewedSpacecraftDetailSerializer,
                             UserSerializer, UserUpdateSerializer, FlightDetailSerializer, FlightSerializer)
from lab.models import SpaceObject, UncrewedSpacecraft, Flight
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes

from rest_framework import mixins
from rest_framework import generics

from django.contrib.auth.models import User

@api_view(['POST'])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key}, status=status.HTTP_200_OK)
    return Response({'error': 'Неверные учетные данные'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_view(request):
    request.user.auth_token.delete()
    logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    user = request.user
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Синглтон для пользователя Creator
def get_creator_user():
    # if not hasattr(get_creator_user, "instance"):
    #     # В settings можно определить ID пользователя creator или другое свойство для поиска
    #     creator_user_id = settings.CREATOR_USER_ID
    #     get_creator_user.instance = User.objects.get(id=creator_user_id)
    # return get_creator_user.instance
    return User.objects.get(pk=1)




class SpaceObjectList(APIView):
    model_class = SpaceObject
    serializer_class = SpaceObjectSerializer
    uncrewed_spacecraft_model_class = UncrewedSpacecraft
    uncrewed_spacecraft_serializer_class = UncrewedSpacecraftSerializer

    # Возвращает список объектов
#     def get(self, request, format=None):
    #         draft_request = self.uncrewed_spacecraft_model_class.objects.filter(
    #             # user=request.user,
    #             # user=get_current_user(),
    #             status='draft').first()
    #         uncrewed_spacecraft_serializer = self.uncrewed_spacecraft_serializer_class(
    #             draft_request, many=False)
    #         space_objects = self.model_class.objects.filter(is_active=True)
    #         serializer = self.serializer_class(space_objects, many=True)
    #         return Response(
    #             {
    #                 'order id': uncrewed_spacecraft_serializer.data['id'],
    #                 'space objects': serializer.data
    #             }
    #         )

    def get(self, request, format=None):
        queryset = self.get_queryset()  # Вызовите ваш метод get_queryset
        draft_request = self.uncrewed_spacecraft_model_class.objects.filter(status='draft').first()
        uncrewed_spacecraft_serializer = self.uncrewed_spacecraft_serializer_class(draft_request, many=False)
        serializer = self.serializer_class(queryset, many=True)
        return Response(
            {
                'order id': uncrewed_spacecraft_serializer.data['id'],
                'space objects': serializer.data
            }
        )

    def get_queryset(self):
            queryset = SpaceObject.objects.all()
            space_object = self.request.query_params.get('space_object', None)

            if space_object:
                queryset = queryset.filter(name=space_object)

            return queryset

    # Добавляет новый объект
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # serializer.save()
            # Указываем создателя заявки как синглтон
            #creator_user = get_creator_user()
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    #def get_queryset(self):
    #    queryset = SpaceObject.objects.all()
    #    space_object = self.request.query_params.get('space_object', None)

    #    if space_object:
    #        queryset = queryset.filter(name=space_object)

    #    return queryset # для пользователя


class SpaceObjectDetail(APIView):
    model_class = SpaceObject
    serializer_class = SpaceObjectDetailSerializer

    # Возвращает информацию об объекте
    def get(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(space_object)
        return Response(serializer.data)

    # Обновляет информацию об объекте (для модератора)
    def put(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(space_object, data=request.data,
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаляет информацию об объекте
    def delete(self, request, pk, format=None):
        space_object = get_object_or_404(self.model_class, pk=pk)
        space_object.delete(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


# class SpaceObjectDetail(mixins.RetrieveModelMixin,
#                         mixins.UpdateModelMixin,
#                         mixins.DestroyModelMixin,
#                         generics.GenericAPIView):
#     queryset = SpaceObject.objects.all()
#     serializer_class = SpaceObjectDetailSerializer
#
#     def get(self, request, *args, **kwargs):
#         return self.retrieve(request, *args, **kwargs)
#
#     def put(self, request, *args, **kwargs):
#         return self.update(request, *args, **kwargs)
#
#     def delete(self, request, *args, **kwargs):
#         return self.destroy(request, *args, **kwargs)


class OrdersList(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 generics.GenericAPIView):
    queryset = UncrewedSpacecraft.objects.all()
    serializer_class = UncrewedSpacecraftSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = UncrewedSpacecraft.objects.all()
        status = self.request.query_params.get('status', None)
        formed_date = self.request.query_params.get('formed_date', None)

        if status:
            queryset = queryset.filter(status=status)
        if formed_date:
            queryset = queryset.filter(created_at__gte=formed_date)

        return queryset.exclude(status='deleted')


    def post(self, request, *args, **kwargs):
        creator_user = request.user  # Создатель заявки — текущий пользователь
        request.data['creator'] = creator_user.id
        request.data['user'] = creator_user.id
        return self.create(request, *args, **kwargs)




class OrderDetail(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                  generics.GenericAPIView):
    queryset = UncrewedSpacecraft.objects.filter(status='draft')
    serializer_class = UncrewedSpacecraftDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        uncrewed_spacecraft = self.get_object()

        # Проверка, является ли пользователь создателем заявки
        if request.user != uncrewed_spacecraft.creator:
            return Response(
                {'error': 'Вы не являетесь создателем этой заявки'},
                status=status.HTTP_403_FORBIDDEN)

        # Обработка данных для SpaceObject
        space_objects_data = request.data.get('space_objects', [])

        # Добавление новых SpaceObject
        for space_object_data in space_objects_data:
            space_object_serializer = SpaceObjectDetailSerializer(
                data=space_object_data)
            if space_object_serializer.is_valid():
                space_object = space_object_serializer.save()
                # Здесь вы можете добавить логику для связывания SpaceObject с UncrewedSpacecraft
                uncrewed_spacecraft.space_objects.add(
                    space_object)  # Предполагается, что у вас есть связь
            else:
                return Response(space_object_serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

        # Обновление UncrewedSpacecraft
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        uncrewed_spacecraft = self.get_object()
        if request.user != uncrewed_spacecraft.creator:
            return Response(
                {'error': 'Вы не являетесь создателем этой заявки'},
                status=status.HTTP_403_FORBIDDEN)
        return self.destroy(request, *args, **kwargs)
    # # Возвращает список услуг в заявке
    # def list(self, request, format=None):
    #     # uncrewed_spacecrafts = self.model_class.objects.all()
    #     uncrewed_spacecrafts = self.model_class.objects.exclude(
    #         status='deleted').exclude(status='draft')
    #     serializer = self.serializer_class(uncrewed_spacecrafts, many=True)
    #     return Response(serializer.data)

    # # Добавляет новую услугу
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlightList(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
                 generics.GenericAPIView):
    queryset = Flight.objects.all()
    serializer_class = FlightSerializer

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class FlightDetail(mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    queryset = Flight.objects.all()
    serializer_class = FlightDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

@api_view(['Put'])
def put(self, request, pk, format=None):
    space_object = get_object_or_404(self.model_class, pk=pk)
    serializer = self.serializer_class(space_object, data=request.data,
                                       partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
