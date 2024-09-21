from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .models import Developer, App, UserAppRegistration, CustomUser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework import viewsets
from .serializers import (
    SerializeApp,
    SerializeCustomUSer,
    SerializeDeveloper,
    SerializeUserAppRegistration,
)
from .permissions import IsAppOwner, IsDeveloper
from mock_auth.settings import SIMPLE_JWT
import jwt


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = SerializeCustomUSer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        else:
            return [IsAuthenticated()]

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Custom user registration action"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class UserAppRegistrationViewSet(viewsets.ModelViewSet):
    queryset = UserAppRegistration.objects.all()
    serializer_class = SerializeUserAppRegistration
    permission_classes = [IsAuthenticated]


class AppViewSet(viewsets.ModelViewSet):
    serializer_class = SerializeApp
    permission_classes = [IsAuthenticated, IsAppOwner]

    def get_queryset(self):
        return App.objects.filter(developer__user=self.request.user)

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), IsDeveloper()]
        elif self.action == "list":
            return [IsAuthenticated(), IsAppOwner()]
        else:
            return [IsAuthenticated(), IsAppOwner(), IsDeveloper()]

    @action(detail=False, methods=["post"])
    def register_app(self, request):
        """App registration action"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        developer = Developer.objects.get(id - self.request.get("developer_id"))
        if not developer:
            return Response(
                {"error": "Developer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        serializer.save(developer=developer)


class DeveloperViewSet(viewsets.ModelViewSet):
    serializer_class = SerializeDeveloper

    def get_queryset(self):
        return Developer.objects.filter(user=self.request.user)

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated()]
        else:
            return [IsAuthenticated(), IsDeveloper()]

    @action(detail=False, methods=["post"])
    def register_developer(self, request):
        """Developer registration action"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if Developer.objects.filter(user=request.user).exists():
            return Response(
                {"error": "Developer already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(user=request.user)
        return Response(serializer.data)


class CustomRefreshToken(RefreshToken):
    @classmethod
    def for_user(cls, user, app_id=None):
        refresh = super().for_user(user)

        if hasattr(user, "developer_profile"):
            developer = Developer.objects.get(user=user)
            refresh["developer_id"] = developer.id
            if developer.stripe_account_id:
                refresh["stripe_account"] = developer.stripe_account_id
            app_ids = developer.apps.values_list("id", flat=True)
            if app_id and app_id in app_ids:
                refresh["app_id"] = app_id
                refresh["app_ids"] = list(app_ids)
            else:
                refresh["app_ids"] = list(app_ids)

        return refresh


@api_view(["POST"])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    app_id = request.data.get("app_id")

    user = authenticate(username=username, password=password)
    if user:
        refresh = CustomRefreshToken.for_user(user, app_id)

        payload = {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }
        return Response(payload, status=status.HTTP_200_OK)

    return Response({"error": "Unauthorized"}, status=401)


#### Confirmation views ####
def decode_token(token):
    try:
        decoded = jwt.decode(
            token, SIMPLE_JWT["SIGNING_KEY"], algorithms=[SIMPLE_JWT["ALGORITHM"]]
        )
        return decoded
    except jwt.DecodeError:
        return None


def confirm_credentials(request):
    """Confirms Credentials"""
    token = request.headers.get("Authorization")
    developer_token = request.headers.get("X-Developer-Token")
    user_token = request.headers.get("X-User-Token")
    developer_id = request.headers.get("X-Developer-ID")
    user_id = request.headers.get("X-User-ID")
    app_id = request.headers.get("X-App-ID")

    payload = {}
    if token and token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
        new_payload = decode_token(token)
        payload.update(new_payload)

    if developer_token and developer_token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
        new_payload = decode_token(token)
        payload.update(new_payload)

    if user_token and user_token.startswith("Bearer "):
        token = token.split("Bearer ")[1]
        new_payload = decode_token(token)
        payload.update(new_payload)

    if developer_id:
        if app_id:
            payload["developer_id"] = developer_id
            payload["app_id"] = app_id
        else:
            payload["developer_id"] = developer_id

    if user_id:
        if app_id:
            payload["user_id"] = user_id
            payload["app_id"] = app_id
        else:
            payload["user_id"] = user_id

    if not payload:
        return Response(
            {"valid": "False", "message": "Invalid token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
    else:
        return payload


@api_view(["GET"])
def confirm_developer(request):
    """Confirms Developer"""
    payload = confirm_credentials(request)
    app_id = (
        payload.get("app_id")
        if payload.get("app_id")
        else request.query_params.get("app_id")
    )
    developer_id = payload.get("developer_id")

    if app_id and type(app_id) == str:
        if payload.get("app_ids"):
            if app_id not in payload["app_ids"]:
                return Response(
                    {
                        "valid": False,
                        "message": f"{['Invalid app_id', 'not in developer app']}",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            else:
                developer = Developer.objects.get(id=developer_id)
                if developer:
                    return Response(
                        {
                            "valid": True,
                            "developer_id": f"{developer_id}",
                            "app_id": f"{app_id}",
                            "message": "Developer confirmed",
                        },
                        status=status.HTTP_200_OK,
                    )

    if developer_id and type(developer_id) == str:
        developer = Developer.objects.get(id=developer_id)
        if developer:
            return Response(
                {
                    "valid": True,
                    "developer_id": f"{developer_id}",
                    "app_id": f"{app_id}",
                    "message": "Developer confirmed",
                },
                status=status.HTTP_200_OK,
            )
    return Response(
        {"valid": False, "message": "Unauthorized"},
        status=status.HTTP_401_UNAUTHORIZED,
    )


@api_view(["GET"])
def confirm_user(request):
    payload = confirm_credentials(request)
    app_id = (
        payload.get("app_id")
        if payload.get("app_id")
        else request.query_params.get("app_id")
    )
    user_id = payload.get("user_id")

    if app_id:
        user = CustomUser.objects.get(id=user_id)
        if user:
            app = App.objects.get(id=app_id)
            if not app:
                return Response(
                    {"valid": False, "message": "Invalid app_id"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            registered = UserAppRegistration.objects.filter(user=user, app=app).exists()
            if registered:
                return Response(
                    {
                        "valid": True,
                        "user_id": f"{user_id}",
                        "app_id": f"{app_id}",
                        "message": "User confirmed",
                    },
                    status=status.HTTP_200_OK,
                )
            if not registered:
                return Response(
                    {
                        "valid": False,
                        "message": f"{['Invalid app_id', 'User not Registered to app']}",
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
    if user_id:
        user = CustomUser.objects.get(id=user_id)
        if user:
            return Response(
                {
                    "valid": True,
                    "user_id": f"{user_id}",
                    "app_id": f"{app_id}",
                    "message": "User confirmed",
                },
                status=status.HTTP_200_OK,
            )
    return Response(
        {"valid": False, "message": "Unauthorized"},
        status=status.HTTP_401_UNAUTHORIZED,
    )
