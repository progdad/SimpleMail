from abc import abstractmethod
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.forms.utils import to_current_timezone
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView, ContextMixin

from .models import Mail, Profile


class UnauthorizedUserMixin(View):
    redirect_url = "login"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.redirect_url)
        return super().dispatch(request, *args, **kwargs)


class LogInUserMixin(TemplateView, View):
    template_name = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("all-received-mails")
        return super().dispatch(request, *args, **kwargs)

    @staticmethod
    def get_user_auth_data(request, *args):
        gotten_objects = list()
        for arg in args:
            arg = arg.strip() if arg == "username" else arg
            arg_value = request.POST.get(arg)
            gotten_objects.append(arg_value)
        return gotten_objects


class MailCreationDatetimeMixin:
    @staticmethod
    def render_field_created(mail: Mail):
        is_today = mail.created.strftime("%d %B %Y") == datetime.today().strftime("%d %B %Y")
        if is_today:
            return "Today at " + to_current_timezone(mail.created).strftime("%H:%M")

        is_yesterday = mail.created.strftime("%d %B %Y") == \
                       datetime.date(datetime.today() - timedelta(days=1)).strftime("%d %B %Y")
        if is_yesterday:
            return "Yesterday at " + to_current_timezone(mail.created).strftime("%H:%M")
        return to_current_timezone(mail.created).strftime("%d %B, %Y at %H:%M")


class DisplayMailsQueryMixin(UnauthorizedUserMixin, MailCreationDatetimeMixin):
    template_name = None
    redirect_url = None
    user = None

    def get(self, request, *args, **kwargs):
        self.request = request

        any_redirection_checkpoint = self._perform_checkpoints()
        if any_redirection_checkpoint:
            return redirect(any_redirection_checkpoint)

        all_mails_or_empty_query = self._render_query_with_all_mails()
        all_zipped_mail_queries = self._set_necessary_data_for_query_context(all_mails_or_empty_query)
        current_page_5_mails_query = self._paginate_mails_by_5_in_each_page_and_get_current_query(all_zipped_mail_queries)

        context = {**current_page_5_mails_query, "searched": self.searched}
        return render(self.request, self.template_name, context)

    def _perform_checkpoints(self):
        if self.request.GET.get("close") is not None:
            return self.redirect_url

        full_url = self.request.build_absolute_uri()
        if "searched=&submit=" in full_url:
            return full_url.replace("?searched=&submit=", '')

    @abstractmethod
    def _render_query_with_all_mails(self):
        self.searched = self.request.GET.get("searched")

    def _set_necessary_data_for_query_context(self, mails):
        profile_pictures = []
        for mail in mails:
            mail.render_field_created = self.render_field_created(mail)
            username = User.objects.get(username=eval(f"mail.{self.user}"))
            avatar = Profile.objects.get(user=username).avatar
            profile_pictures.append(avatar)
        return list(zip(mails, profile_pictures))

    def _paginate_mails_by_5_in_each_page_and_get_current_query(self, mails):
        current_page_number = self.request.GET.get("page")
        paginator = Paginator(mails, 5)
        current_query = paginator.get_page(current_page_number)
        return {"mails": current_query, "flag": True}


class ProfileDatetimeCreationMixin:
    @property
    def joined(self: Profile):
        datetime_joined = self.user.date_joined.strftime("%d %B %Y")

        is_today = datetime_joined == datetime.today().strftime("%d %B %Y")
        if is_today:
            return "today"

        is_yesterday = datetime_joined == datetime.date(datetime.today() - timedelta(days=1)).strftime("%d %B %Y")
        if is_yesterday:
            return "yesterday"
        return str(to_current_timezone(self.user.date_joined).strftime('%d %B %Y'))
