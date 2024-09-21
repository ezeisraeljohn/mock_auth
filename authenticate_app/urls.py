from django.urls import path
from .views import login_view, confirm_developer, confirm_user
from rest_framework.routers import DefaultRouter
from .views import (
    CustomUserViewSet,
    AppViewSet,
    DeveloperViewSet,
    UserAppRegistrationViewSet,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()

urlpatterns = [
    path("login/", login_view, name="login"),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("confirm/developer/", confirm_developer, name="confirm_developer"),
    path("confirm/user/", confirm_user, name="confirm_developer"),
]

router.register(r"users", CustomUserViewSet)
router.register(r"apps", AppViewSet, basename="app")
router.register(r"developers", DeveloperViewSet, basename="developer")
router.register(r"registrations", UserAppRegistrationViewSet)

urlpatterns += router.urls
