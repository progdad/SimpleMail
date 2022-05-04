from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .models import Mail, Profile


def mails_counter(request):

    if not request.user.is_authenticated:
        return None, None, None

    user = request.user

    received_mails_counter = Mail.objects.filter(to_user=user).count()
    sent_mails_counter = Mail.objects.filter(from_user=user).count()
    unvisited_received_mails_counter = Mail.objects.filter(to_user=user, unvisited=True).count()

    return received_mails_counter, sent_mails_counter, unvisited_received_mails_counter


