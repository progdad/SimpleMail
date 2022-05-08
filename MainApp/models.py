from django.db import models
from django.contrib.auth.models import User


def username(user, file):
    string_username = str(user).split()[0]
    return f"profiles/{string_username}/{file}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="Profile")
    avatar = models.ImageField(default="/profiles/default.png", upload_to=username)
    name = models.CharField(max_length=30, blank=True)
    surname = models.CharField(max_length=30, blank=True)
    email = models.EmailField(max_length=64, blank=True)
    bio = models.CharField(max_length=1024, blank=True)

    def __str__(self):
        return f"{self.user} profile"


class Mail(models.Model):
    title = models.CharField(max_length=64)
    body = models.CharField(max_length=1000)
    unvisited = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    to_user = models.ForeignKey(User, related_name="ToUser", on_delete=models.SET_NULL, null=True)
    from_user = models.ForeignKey(User, related_name="FromUser", on_delete=models.SET_NULL, null=True)
    from_user_inf = models.CharField(max_length=30)
    to_user_inf = models.CharField(max_length=30)

    def __str__(self):
        return f"\"{self.title[:25]}\" from {self.from_user_inf} to {self.to_user_inf}"

    class Meta:
        ordering = ["-created"]
