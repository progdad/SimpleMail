from django.contrib.auth.models import AnonymousUser
from .views_settings import mails_counter
from .models import Profile


def sidebar_mails(request):
    mails_info = mails_counter(request)
    context = {
        "received_mails_counter":    mails_info[0],
        "sent_mails_counter":        mails_info[1],
        "unvisited_mails_counter":   mails_info[2],
    }

    if not isinstance(request.user, AnonymousUser):
        profile = Profile.objects.get(user=request.user)
        context['host_avatar'] = profile.avatar
        
    return context
