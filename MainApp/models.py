from django.db import models
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.forms.utils import to_current_timezone


def username(user, file):
    string_username = str(user).split()[0]
    return f"profiles/{string_username}/{file}"


class Profile(models.Model):
    user                 = models.OneToOneField(User, on_delete=models.CASCADE, related_name="Profile")
    avatar               = models.ImageField(default="/profiles/default.png", upload_to=username)
    
    name                 = models.CharField(max_length=30, blank=True)
    surname              = models.CharField(max_length=30, blank=True)

    email                = models.EmailField(max_length=64, blank=True)
    bio                  = models.CharField(max_length=1024, blank=True)

    def username(self):
        return self.user.username

    @property
    def joined(self):

        joined = self.user.date_joined.strftime("%d %B %Y")

        is_today = joined == datetime.today().strftime("%d %B %Y")
        if is_today:
            return "today"

        is_yesterday = joined == datetime.date(datetime.today() - timedelta(days=1)).strftime("%d %B %Y")  
        if is_yesterday:
            return "yesterday"

        return f"{to_current_timezone(self.user.date_joined).strftime('%d %B %Y')}"

    def __str__(self):
        return f"{self.user} profile"


class Mail(models.Model):
    title     = models.CharField(max_length=128)
    body      = models.CharField(max_length=9999)

    unvisited = models.BooleanField(default=True)
    created   = models.DateTimeField(auto_now_add=True)

    to_user   = models.ForeignKey(
        User,
        related_name="ToUser",
        on_delete=models.SET_NULL,
        null=True
    )

    from_user = models.ForeignKey(
        User,
        related_name="FromUser",
        on_delete=models.SET_NULL,
        null=True
    )

    from_user_inf       = models.CharField(max_length=30)
    to_user_inf         = models.CharField(max_length=30)

    @property
    def render_created(self): 
        is_today = self.created.strftime("%d %B %Y") == datetime.today().strftime("%d %B %Y")
        
        if is_today:
            return "Today at " + to_current_timezone(self.created).strftime("%H:%M")

        is_yesterday = self.created.strftime("%d %B %Y") == datetime.date(datetime.today() - timedelta(days=1)).strftime("%d %B %Y")

        if is_yesterday:
            return "Yesterday at " + to_current_timezone(self.created).strftime("%H:%M")

        return to_current_timezone(self.created).strftime("%d %B, %Y at %H:%M")

    def __str__(self):
        return f"\"{self.title[:25]}\" от {self.from_user_inf} для {self.to_user_inf}"

    class Meta:
        ordering = ["-created"]
