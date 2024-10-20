from rest_framework import serializers
from django.core.exceptions import ValidationError
from api.models import SpaceObject, UncrewedSpacecraft, FlightSpaceObject, \
    AuthUser
from collections import OrderedDict


class SpaceObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpaceObject
        # fields = '__all__'
        fields = ['id', 'name', 'description', 'image_url']

        def get_fields(self):
            new_fields = OrderedDict()
            for name, field in super().get_fields().items():
                field.required = False
                new_fields[name] = field
            return new_fields


class FlightSpaceObjectSerializer(serializers.ModelSerializer):
    space_object = SpaceObjectSerializer()

    class Meta:
        model = FlightSpaceObject
        # fields = '__all__'
        fields = ['id', 'space_object', 'create_date', 'completed_successfully']


class SpacecraftSerializer(serializers.ModelSerializer):
    space_objects = FlightSpaceObjectSerializer(many=True, read_only=True)
    space_object_count = serializers.SerializerMethodField()

    class Meta:
        model = UncrewedSpacecraft
        fields = '__all__'

    def get_space_object_count(self, obj):
        return obj.space_objects.count()


class SpacecraftSerializerForList(serializers.ModelSerializer):
    # space_objects = FlightSpaceObjectSerializer(many=True, read_only=True)
    # space_object_count = serializers.SerializerMethodField()

    class Meta:
        model = UncrewedSpacecraft
        fields = '__all__'

    # def get_space_object_count(self, obj):
    #     return obj.space_objects.count()


class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
    # space_objects = FlightSpaceObjectSerializer(many=True, read_only=True)

    class Meta:
        model = AuthUser
        fields = (
        'id', 'email', 'password', 'first_name', 'last_name', 'is_superuser',
        'is_staff')
        extra_kwargs = {
            'email': {'required': True},
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def create(self, validated_data):
        if AuthUser.objects.filter(
                email=validated_data['email']).exists():
            raise ValidationError(
                "Пользователь с таким email уже существует.")

        user = AuthUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthUser
        fields = ['email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        # instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.save()
        return instance

    def get_fields(self):
        new_fields = OrderedDict()
        for name, field in super().get_fields().items():
            field.required = False
            new_fields[name] = field
        return new_fields
