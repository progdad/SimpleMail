from django.contrib.auth.models import AnonymousUser
from .models import Mail, Profile


def sidebar_and_avatar(request):
    mails_info = _mails_counter(request)
    context = {
        "received_mails_counter": mails_info[0],
        "sent_mails_counter": mails_info[1],
        "unvisited_mails_counter": mails_info[2],
    }
    if not isinstance(request.user, AnonymousUser):
        profile = Profile.objects.get(user=request.user)
        context['host_avatar'] = profile.avatar
    return context


def _mails_counter(request):
    if not request.user.is_authenticated:
        return None, None, None
    user = request.user
    received_mails_counter = Mail.objects.filter(to_user=user).count()
    sent_mails_counter = Mail.objects.filter(from_user=user).count()
    unvisited_received_mails_counter = Mail.objects.filter(to_user=user, unvisited=True).count()
    return received_mails_counter, sent_mails_counter, unvisited_received_mails_counter
