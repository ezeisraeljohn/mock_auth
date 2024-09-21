from .models import CustomUser, Developer, App, UserAppRegistration
from rest_framework import serializers
from django.contrib.auth.hashers import make_password


from .models import CustomUser, Developer, App, UserAppRegistration
from rest_framework import serializers
from django.contrib.auth.hashers import make_password


class SerializeCustomUSer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "address",
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data.get("password"))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.get("password", None)
        if password:
            instance.password = make_password(password)
        return super().update(instance, validated_data)


class SerializeDeveloper(serializers.ModelSerializer):
    apps = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Developer
        fields = "__all__"

        def create(self, validated_data):
            return super().create(validated_data)


class SerializeApp(serializers.ModelSerializer):
    developers = SerializeDeveloper(read_only=True)
    users_registered = serializers.PrimaryKeyRelatedField(
        many=True, read_only=True, source="registrations.user"
    )

    class Meta:
        model = App
        fields = [
            "id",
            "name",
            "description",
            "developers",
            "users_registered",
            "developer",
        ]

        def create(self, validated_data):
            return super().create(validated_data)


class SerializeUserAppRegistration(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all())
    app = serializers.PrimaryKeyRelatedField(queryset=App.objects.all())

    class Meta:
        model = UserAppRegistration
        fields = ["user", "app", "registration_date"]

    def create(self, validated_data):
        user = validated_data.get("user")
        app = validated_data.get("app")

        if UserAppRegistration.objects.filter(user=user, app=app).exists():
            raise serializers.ValidationError("User is already registered to this app.")

        return UserAppRegistration.objects.create(**validated_data)
