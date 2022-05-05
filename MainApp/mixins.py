from __future__ import annotations

from abc import abstractmethod
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.forms.utils import to_current_timezone
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic.base import TemplateView

from .models import Mail, Profile


class UnauthorizedUserMixin(View):
    def dispatch(self, request, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        return super().dispatch(request)


class LogInUserMixin(TemplateView, View):
    template_name = None

    def dispatch(self, request, **kwargs):
        if request.user.is_authenticated:
            return redirect("all-received-mails")
        return super().dispatch(request, **kwargs)

    @staticmethod
    def get_user_form_data(request, *args):
        gotten_objects = list()
        for arg in args:
            arg = arg.strip() if arg == "username" else arg
            arg_value = request.POST.get(arg)
            gotten_objects.append(arg_value)
        return gotten_objects


class DatetimeCreationMixin:
    def render_field_created(self, datetm):
        datetime_created = datetm.strftime("%d %B %Y")

        is_today = datetime_created == datetime.today().strftime("%d %B %Y")
        if is_today:
            return self._render_previous_two_days_datetime(day="today", datetm=datetm)

        is_yesterday = datetime_created == datetime.date(datetime.today() - timedelta(days=1)).strftime("%d %B %Y")
        if is_yesterday:
            return self._render_previous_two_days_datetime(day="yesterday", datetm=datetm)
        return self._render_old_datetime(datetm)

    @abstractmethod
    def _render_previous_two_days_datetime(self, **kwargs):
        pass

    @abstractmethod
    def _render_old_datetime(self, datetm):
        pass


class MailDatetimeCreationMixin(DatetimeCreationMixin):
    def _render_previous_two_days_datetime(self, day, datetm):
        return f"{day} at " + to_current_timezone(datetm).strftime("%H:%M")

    def _render_old_datetime(self, datetm):
        return to_current_timezone(datetm).strftime("%d %B, %Y at %H:%M")


class DisplayMailsQueryMixin(View, MailDatetimeCreationMixin):
    template_name = None
    redirect_url = None
    user = None

    def dispatch(self, request, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        full_url = request.build_absolute_uri()
        if "searched=&submit=" in full_url:
            return redirect(full_url.replace("?searched=&submit=", ''))
        return super().dispatch(request)

    def get(self, request):
        self.request = request

        if self.request.GET.get("close") is not None:
            return redirect(self.redirect_url)

        all_mails_or_empty_query = self._render_query_with_all_mails()
        all_zipped_mail_queries = self._set_necessary_data_for_query_context(all_mails_or_empty_query)
        current_page_5_mails_query = self._paginate_mails_by_5_in_each_page_and_get_current_query(all_zipped_mail_queries)

        context = {**current_page_5_mails_query, "searched": self.searched}
        return render(self.request, self.template_name, context)

    @abstractmethod
    def _render_query_with_all_mails(self):
        self.searched = self.request.GET.get("searched")

    def _set_necessary_data_for_query_context(self, mails):
        profile_pictures = []
        for mail in mails:
            mail.render_field_created = self.render_field_created(mail.created)
            username = User.objects.get(username=getattr(mail, self.user))
            avatar = Profile.objects.get(user=username).avatar
            profile_pictures.append(avatar)
        return list(zip(mails, profile_pictures))

    def _paginate_mails_by_5_in_each_page_and_get_current_query(self, mails):
        current_page_number = self.request.GET.get("page")
        paginator = Paginator(mails, 5)
        current_query = paginator.get_page(current_page_number)
        return {"mails": current_query, "flag": True}


class VisitMailMixin(View, MailDatetimeCreationMixin):
    template_name = None
    redirect_url = None
    user = None
    participant_inf = None

    def dispatch(self, request, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        pk = kwargs.get("pk", -1)
        self.mail = self._try_to_get_current_mail_object(pk)
        if not self.mail:
            return redirect(self.redirect_url)

        if getattr(self.mail, self.user) != self.request.user:
            return redirect(self.redirect_url)
        return super().dispatch(request)

    def get(self, request):
        username = getattr(self.mail, self.participant_inf)
        user = User.objects.get(username=username)
        avatar = Profile.objects.get(user=user).avatar

        self.mail.render_field_created = self.render_field_created(self.mail.created)
        context = {"mail": self.mail, "avatar": avatar}
        return render(request, self.template_name, context)

    def post(self, request):
        if request.POST.get("Delete"):
            setattr(self.mail, self.user, None)
            self.mail.save()
        return redirect(self.redirect_url)

    @staticmethod
    @abstractmethod
    def _try_to_get_current_mail_object(pk):
        pass


class GetProfileContextMixin(View, DatetimeCreationMixin):
    def dispatch(self, request, user=None, **kwargs):
        try:
            context = self._get_user_info_and_create_context(user)
            return super().dispatch(request, **context)
        except ObjectDoesNotExist:
            return redirect("all-received-mails")

    def _get_user_info_and_create_context(self, user):
        profile = Profile.objects.get(user=user)
        sent_messages = Mail.objects.filter(from_user_inf=user).count()
        received_messages = Mail.objects.filter(to_user_inf=user).count()

        profile.joined = self.render_field_created(profile.user.date_joined)
        context = {
            "profile": profile,
            "sent": sent_messages,
            "received": received_messages,
        }
        return context

    def _render_previous_two_days_datetime(self, **kwargs):
        return kwargs["day"]

    def _render_old_datetime(self, datetm):
        return to_current_timezone(datetm).strftime("%d %B, %Y")
