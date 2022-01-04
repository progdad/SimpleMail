from django.urls import path

from django.conf.urls.static import static
from django.conf import settings

from . import views


urlpatterns = [
    path('', views.home, name="home"),

    path('signup/', views.register, name='signup'),
    path('login/', views.log_in, name='login', ),
    path('logout/', views.log_out, name='logout'),

    path('my-profile', views.my_profile, name='my-profile'),
    path('profile/<str:username>/', views.user_profile, name='profile'),

    path('new-mail/', views.new_mail, name="send-mail"),

    path('sent-mails/', views.all_sent_mails, name='all-sent-mails'),
    path('sent-mail/<str:pk>/', views.sent_mail, name='sent-mail'),
    
    path('received-mails/', views.all_received_mails, name='all-received-mails'),
    path('received-mail/<str:pk>/', views.received_mail, name='received-mail'),
]

handler404 = "MainApp.views.handler_404"
handler500 = "MainApp.views.handler_500"

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
