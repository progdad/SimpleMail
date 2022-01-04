from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .models import Mail, Profile


def valid_registration(username: str, password1: str, password2: str):

    if not (username and password1 and password2):
        return "Some fields are empty !"

    if User.objects.filter(username=username):
        return "This username is already taken !"

    if not (4 <= len(username) <= 24):
        return "Username can be only from 4 to 24 characters long !"

    if not (username[0].isalpha() and username.isalnum()):
        return "Incorrect username !"

    if not (password1 == password2 and 8 <= len(password1) <= 64):
        return "Passwords didn't match or incorrect password length !"

    return "Correct"


def mails_counter(request):

    if not request.user.is_authenticated:
        return None, None, None

    user = request.user

    received_mails_counter =                    Mail.objects.filter(to_user=user).count()
    sent_mails_counter =                        Mail.objects.filter(from_user=user).count()    
    unvisited_received_mails_counter =          Mail.objects.filter(to_user=user, unvisited=True).count()

    return received_mails_counter, sent_mails_counter, unvisited_received_mails_counter
    

def mails_settings(request, user, mails):

    profile_pictures = []
    for mail in mails:
        usernm = User.objects.get(username=eval(f"mail.{user}"))
        avatar = Profile.objects.get(user=usernm).avatar
        profile_pictures.append(avatar)

    mails = list(zip(mails, profile_pictures))
    current_page_number = request.GET.get("page")
    paginator = Paginator(mails, 5)
    current_query = paginator.get_page(current_page_number)

    context = {
        "mails": current_query,
        "flag": True
    }

    request_full_path = request.build_absolute_uri()
    if 'searched=' in request_full_path:
        starts = request_full_path.find("searched=")
        ends = request_full_path[starts:].find('&')
        if ends != -1:
            searched = request_full_path[starts:starts + ends]
        else:
            searched = request_full_path[starts:]

        context["searched"] = searched.replace("searched=", '')

    return context

