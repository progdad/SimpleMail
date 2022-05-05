from django.urls import path

from django.conf.urls.static import static
from django.conf import settings

from .views import *


urlpatterns = [
    path('', home, name="home"),

    path('signup/', registration, name='signup'),
    path('login/', login_view, name='login', ),
    path('logout/', logout_view, name='logout'),

    path('new-mail/', send_mail, name="send-mail"),
    path('sent-mails/', sent_mails, name='all-sent-mails'),
    path('received-mails/', received_mails, name='all-received-mails'),
    path('sent-mail/<str:pk>/', sent_mail, name='sent-mail'),
    path('received-mail/<str:pk>/', received_mail, name='received-mail'),

    path('my-profile', my_profile, name='my-profile'),
    path('profile/<str:username>/', user_profile, name='profile'),
]

handler404 = "MainApp.views.handler_404"
handler500 = "MainApp.views.handler_500"

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
