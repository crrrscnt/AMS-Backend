from django.contrib.auth.models import User
from rest_framework import serializers
from django.core.exceptions import ValidationError
from lab.models import SpaceObject, UncrewedSpacecraft, Flight

'''
Простые реализации по умолчанию для методов create() и update().
https://ilyachch.gitbook.io/django-rest-framework-russian-documentation/overview/quickstart/1-serialization
'''


class SpaceObjectSerializer(serializers.ModelSerializer):
    class Meta:
        # Модель, которую мы сериализуем
        model = SpaceObject
        # Поля, которые мы сериализуем
        # fields = '__all__'
        fields = ('id', 'name', 'uncrewed_spacecraft', 'description', 'price', 'scheduled_at',
                  'image_url')


class SpaceObjectDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceObject
        fields = '__all__'
        # fields = ('id', 'name', 'ais', 'scheduled_at')


class UncrewedSpacecraftSerializer(serializers.ModelSerializer):
    space_objects = SpaceObjectDetailSerializer(many=True, read_only=True)

    class Meta:
        model = UncrewedSpacecraft
        fields = '__all__'
        # fields = ('id', )


class UncrewedSpacecraftDetailSerializer(serializers.ModelSerializer):
    space_objects = SpaceObjectDetailSerializer(many=True, read_only=True)

    class Meta:
        model = UncrewedSpacecraft
        fields = '__all__'


class FlightSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = '__all__'

class FlightDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flight
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        if User.objects.filter(username=validated_data['username']).exists():
            raise ValidationError(
                "Пользователь с таким именем уже существует.")
        if User.objects.filter(email=validated_data['email']).exists():
            raise ValidationError(
                "Пользователь с таким адресом электронной почты уже существует.")

        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user



class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance
