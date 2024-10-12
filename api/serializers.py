from django.contrib.auth.models import User
from rest_framework import serializers
from django.core.exceptions import ValidationError
from lab.models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject, \
    AuthUser
from django.contrib.auth.hashers import make_password


class SpaceObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceObject
        fields = '__all__'
        # fields = ('id', 'name', 'description', 'image_url')


class SpaceObjectSerializer2(serializers.ModelSerializer):
    class Meta:
        model = SpaceObject
        fields = ('name', 'image_url')


class FlightSpaceObjectSerializer(serializers.ModelSerializer):
    space_object = SpaceObjectSerializer()

    class Meta:
        model = FlightSpaceObject
        # fields = '__all__'
        fields = ['id', 'space_object', 'create_date', 'is_priority']

class FlightSpaceObjectSerializer2(serializers.ModelSerializer):
    space_object = SpaceObjectSerializer2()

    class Meta:
        model = FlightSpaceObject
        # fields = '__all__'
        fields = ['id', 'space_object', 'create_date', 'is_priority']

class SpacecraftSerializer(serializers.ModelSerializer):
    space_objects = FlightSpaceObjectSerializer2(many=True, read_only=True)
    object_count = serializers.SerializerMethodField()

    class Meta:
        model = UncrewedSpacecraft
        fields = '__all__'

    def get_object_count(self, obj):
        return obj.space_objects.count()


class UserSerializer(serializers.ModelSerializer):
    space_objects = FlightSpaceObjectSerializer(many=True, read_only=True)
    class Meta:
        model = AuthUser
        fields = ('id','username', 'email', 'password', 'space_objects')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        if AuthUser.objects.filter(username=validated_data['username']).exists():
            raise ValidationError(
                "Пользователь с таким именем уже существует.")
        if AuthUser.objects.filter(email=validated_data['email']).exists():
            raise ValidationError(
                "Пользователь с таким адресом электронной почты уже существует.")

        validated_data['password'] = make_password(validated_data['password'])
        user = AuthUser.objects.create(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        # fields = ('username', 'email', 'password')
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        instance.username = validated_data.get('username', instance.username)
        # instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance
