from django.urls import path

from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import TemplateView

from .views import *


urlpatterns = [
    path('', HomeView.as_view(), name="home"),

    path('signup/', RegisterUserView.as_view(), name='signup'),
    path('login/', LoginUserView.as_view(), name='login', ),
    path('logout/', LogoutUserView.as_view(), name='logout'),

    path('my-profile', my_profile, name='my-profile'),
    path('profile/<str:username>/', user_profile, name='profile'),

    path('new-mail/', SendMailView.as_view(), name="send-mail"),

    path('sent-mails/', AllSentMailsView.as_view(), name='all-sent-mails'),
    path('sent-mail/<str:pk>/', SentMailView.as_view(), name='sent-mail'),
    
    path('received-mails/', AllReceivedMailsView.as_view(), name='all-received-mails'),
    path('received-mail/<str:pk>/', ReceivedMailView.as_view(), name='received-mail'),
]

handler404 = "MainApp.views.handler_404"
handler500 = "MainApp.views.handler_500"

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
