from django.db import models
from django.contrib.auth.models import AbstractUser
from nanoid import generate


def generate_unique_user_id():
    return f"usr_{generate(size=25)}"


def generate_unique_developer_id():
    return f"de_{generate(size=25)}"


def generate_unique_app_id():
    return f"ap_{generate(size=25)}"


def generate_unique_registration_id():
    return f"re_{generate(size=25)}"


class CustomUser(AbstractUser):
    id = models.CharField(
        primary_key=True,
        default=generate_unique_user_id,
        editable=False,
        max_length=255,
    )
    phone_number = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)


class Developer(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_unique_developer_id,
        editable=False,
        max_length=255,
    )
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name="developer_profile"
    )
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    company_name = models.CharField(max_length=255)

    def __str__(self):
        return self.company_name


class App(models.Model):
    id = models.CharField(
        primary_key=True, default=generate_unique_app_id, editable=False, max_length=255
    )
    name = models.CharField(max_length=255)
    developer = models.ForeignKey(
        Developer, on_delete=models.CASCADE, related_name="apps", null=False
    )
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class UserAppRegistration(models.Model):
    id = models.CharField(
        primary_key=True,
        default=generate_unique_registration_id,
        editable=False,
        max_length=255,
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="registrations"
    )
    app = models.ForeignKey(App, on_delete=models.CASCADE, related_name="registrations")
    registration_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "app")

    def __str__(self):
        return f"{self.user.username} registered for {self.app.name}"
