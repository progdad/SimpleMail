from abc import ABC

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from django.db.models import Q
from django.views import View
from django.views.generic import ListView, DetailView, TemplateView

from .mixins import LogInUserMixin, UnauthorizedUserMixin, DisplayMailsQueryMixin, VisitMailMixin
from .models import Mail, Profile
from .forms import ProfileForm


class HomeView(TemplateView):
    template_name = "home.html"


class RegisterUserView(LogInUserMixin):
    template_name = "signup.html"

    def post(self, request, *args, **kwargs):
        username, password1, password2 = super().get_user_auth_data(request, "username", "password1", "password2")

        form_response = self._valid_registration_data(username, password1, password2)
        if form_response != "Correct":
            context_data = {
                "register_error": form_response, "username": username,
                "password1": password1, "password2": password2
            }
            return render(request, 'signup.html', context_data)

        self._create_new_profile(request, username, password1)
        return redirect("all-received-mails")

    @staticmethod
    def _valid_registration_data(username: str, password1: str, password2: str):
        if not (username and password1 and password2):
            return "Some fields are empty !"
        if User.objects.filter(username=username):
            return "This username is already taken !"
        if not (4 <= len(username) <= 24):
            return "Username can be only from 4 to 24 characters long !"
        if not (username[0].isalpha() and username.isalnum()):
            return "Incorrect username !"
        if not ((password1 == password2) and (8 <= len(password1) <= 64)):
            return "Passwords didn't match or incorrect password length !"
        return "Correct"

    @staticmethod
    def _create_new_profile(request, username, password):
        user = User.objects.create_user(username=username, password=password)
        user.save()
        profile = Profile(user=user)
        profile.save()
        login(request, user)


class LoginUserView(LogInUserMixin):
    template_name = "login.html"

    def post(self, request, *args, **kwargs):
        username, password = super().get_user_auth_data(request, "username", "password")
        user = authenticate(username=username, password=password)

        if not user:
            context = {'username': username, 'password': password, 'login_error': 'Username or password is incorrect !'}
            return render(request, self.template_name, context)

        self._create_user_profile(request, user)

        login(request, user)
        return redirect('all-received-mails')

    @staticmethod
    def _create_user_profile(request, user):
        try:
            Profile.objects.get(user=user)
        except ObjectDoesNotExist:
            profile = Profile(user=user)
            profile.save()


class LogoutUserView(UnauthorizedUserMixin):
    @staticmethod
    def get(request, *args, **kwargs):
        return render(request, "logout.html")

    @staticmethod
    def post(request, *args, **kwargs):
        if request.POST.get("Logout"):
            logout(request)
            return redirect("login")
        return redirect("all-received-mails")


class SendMailView(TemplateView, UnauthorizedUserMixin):
    template_name = "new_mail.html"

    def post(self, request, *args, **kwargs):
        self.request = request
        if self.request.POST.get("back"):
            return redirect("all-sent-mails")

        all_data_validation_methods = [
            self._check_if_not_all_fields_are_filled, self._check_if_recipient_doesnt_exists,
            self._check_if_sender_is_equal_to_recipient, self._check_if_input_fields_are_too_long
        ]

        self.form = dict(self.request.POST.items())
        for validation_method in all_data_validation_methods:
            error = validation_method()
            if error:
                return render(self.request, self.template_name, {"form": self.form, "error": error})

        self.save_and_send_mail()
        return redirect("all-sent-mails")

    def _check_if_not_all_fields_are_filled(self):
        if not all(self.form.values()):
            return "Looks like some fields are empty !"

    def _check_if_recipient_doesnt_exists(self):
        try:
            self.to_user = User.objects.get(username=self.form["to_user"])
        except ObjectDoesNotExist:
            return f"No such user - \"{self.form['to_user']}\""

    def _check_if_sender_is_equal_to_recipient(self):
        self.from_user = User.objects.get(username=self.request.user)
        if self.from_user == self.to_user:
            return "You are trying to send mail to yourself !"

    def _check_if_input_fields_are_too_long(self):
        title_length = len(self.form["title"])
        body_length = len(self.form["body"])
        if title_length > 64:
            return f"The title is too long. Now it's {title_length}, but maximum size is 64 characters"
        if body_length > 1000:
            return f"Your text message is too big. Now it's {body_length}, but maximum size is 1000 characters"

    def save_and_send_mail(self):
        new_mail = Mail()
        new_mail.to_user = self.to_user
        new_mail.from_user = self.from_user
        new_mail.title = self.form["title"]
        new_mail.body = self.form["body"]
        new_mail.to_user_inf = self.to_user.username
        new_mail.from_user_inf = self.from_user.username
        new_mail.save()


class AllSentMailsView(DisplayMailsQueryMixin):
    template_name = "sent_mails.html"
    redirect_url = "all-sent-mails"
    user = "to_user_inf"

    def _render_query_with_all_mails(self):
        super()._render_query_with_all_mails()
        if self.searched:
            return Mail.objects.filter(from_user=self.request.user).filter(
                Q(to_user__username__icontains=self.searched) | Q(title__icontains=self.searched))
        else:
            return Mail.objects.filter(from_user=self.request.user)


class AllReceivedMailsView(DisplayMailsQueryMixin):
    template_name = "received_mails.html"
    redirect_url = "all-received-mails"
    user = "from_user_inf"

    def _render_query_with_all_mails(self):
        super()._render_query_with_all_mails()
        if self.searched:
            return Mail.objects.filter(to_user=self.request.user).filter(
                Q(from_user__username__icontains=self.searched) | Q(title__icontains=self.searched))
        else:
            return Mail.objects.filter(to_user=self.request.user)


class SentMailView(VisitMailMixin):
    template_name = "sent_mail.html"
    redirect_url = "all-sent-mails"
    user = "from_user"
    participant_inf = "to_user_inf"

    @staticmethod
    def _try_to_get_current_mail_object(pk):
        try:
            return Mail.objects.get(id=pk)
        except ObjectDoesNotExist:
            pass


class ReceivedMailView(VisitMailMixin):
    template_name = "received_mail.html"
    redirect_url = "all-received-mails"
    user = "to_user"
    participant_inf = "from_user_inf"

    @staticmethod
    def _try_to_get_current_mail_object(pk):
        try:
            mail = Mail.objects.get(id=pk)
            if mail.unvisited:
                mail.unvisited = False
                mail.save()
            return mail
        except ObjectDoesNotExist:
            pass


def my_profile(request):

    if not request.user.is_authenticated:
        return redirect('login') 

    try:
        my_profile_var = Profile.objects.get(user=request.user)
    except ObjectDoesNotExist:  # another one handler because of a superuser which profile will be created by the code below
        profile = Profile(user=request.user)
        profile.save()
        my_profile_var = Profile.objects.get(user=request.user)

    sent_messages = Mail.objects.filter(from_user_inf=request.user).count()
    received_messages = Mail.objects.filter(to_user_inf=request.user).count()

    context = {
        "profile": my_profile_var,
        "sent": sent_messages, 
        "received": received_messages,
        "date_joined": my_profile_var
    }
    if request.method == 'POST':
        form = ProfileForm(
            request.POST, files=request.FILES, instance=my_profile_var
        )

        if form.is_valid():
            form.save()
            messages.info(request, "Saved successfully !")
            return redirect('my-profile')
        messages.error(request, "Wrong data !") 
    
    form = ProfileForm(instance=my_profile_var)
    context['form'] = form
    return render(request, 'my_profile.html', context=context)


def user_profile(request, username):

    if not request.user.is_authenticated:
        return redirect('login') 

    try:
        user = User.objects.get(username=username)
        if user == request.user:
            return redirect('my-profile')

        usr_profile         = Profile.objects.get(user=user)
        sent_messages       = Mail.objects.filter(from_user_inf=username).count()
        received_messages   = Mail.objects.filter(to_user_inf=username).count()

        context = {
            "profile":   usr_profile,
            "sent":      sent_messages, 
            "received":  received_messages
        }
        return render(request, 'user_profile.html', context=context)
    
    except ObjectDoesNotExist:
        return redirect("all-received-mails")


# Error handlers


def handler_404(request, exception):
    pass


def handler_500(request):
    pass
