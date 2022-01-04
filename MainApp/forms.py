from django import forms
from django.contrib.auth import models
from django.forms import fields
from .models import Profile


class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = "__all__"
        exclude = ("user",)
