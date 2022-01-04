from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User

from django.shortcuts import render, redirect
from django.db.models import Q

from .models import Mail, Profile
from .forms import ProfileForm
from .views_settings import valid_registration, mails_settings


def home(request):
    return render(request, 'home.html')


def register(request):
    if request.user.is_authenticated:
        return redirect("all-received-mails")

    if request.method == 'POST':        
        username = request.POST.get("username").strip()
        password1, password2 = request.POST.get("password1"), request.POST.get("password2")
        form_response = valid_registration(username, password1, password2)

        if form_response == "Correct":  
            user = User.objects.create_user(username=username, password=password1)
            user.save()
            login(request, user)
            profile = Profile(user=user)
            profile.save()
            return redirect("all-received-mails")

        new_data = {
            "register_error": form_response,
            "username": username,
            "password1": password1,
            "password2": password2 
        }
        return render(request, 'signup.html', new_data)

    return render(request, 'signup.html')


def log_in(request):
    if request.user.is_authenticated:
        return redirect("all-received-mails")

    if request.method == "POST":
        username = request.POST.get("username").strip()
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            context = {'username': username, 'password': password,
                       'login_error': 'Username or password are incorrect !'}

            return render(request, "login.html", context=context)

        else:
            login(request, user)
            return redirect('all-received-mails')

    return render(request, "login.html")


def log_out(request):

    if not request.user.is_authenticated:
        return redirect('login') 

    if request.method == "POST":
        if request.POST.get("Logout"):
            logout(request)
            return redirect("login")
        return redirect("all-received-mails")
    
    return render(request, 'logout.html')    


def new_mail(request):

    if not request.user.is_authenticated:
        return redirect('login') 

    if request.method == 'POST':
        if request.POST.get("back"):
            return redirect("all-sent-mails")

        form = dict(request.POST.items())

        if all(form.values()):
            new_mail = Mail()
            from_user = User.objects.get(username=request.user)
            
            try:
                to_user = User.objects.get(username=form["to_user"])
            except ObjectDoesNotExist:
                error = f"No such user - \"{form['to_user']}\""
                context = {
                    'form': form,
                    'error': error
                }
                return render(request, 'new_mail.html', context)

            if from_user == to_user:
                error = f"You are trying to send message to yourself !"
                context = {
                    'form': form,
                    'error': error
                }
                return render(request, "new_mail.html", context)

            new_mail.to_user = to_user
            new_mail.from_user = request.user

            new_mail.title = form["title"]
            new_mail.body = form["body"]

            new_mail.to_user_inf = form["to_user"]
            new_mail.from_user_inf = str(request.user)
            new_mail.save()

            return redirect("all-sent-mails")

        else:
            error = "Looks like some fields are empty !"
            context = {
                'form': form,
                'error': error
            }
            return render(request, 'new_mail.html', context)

    return render(request, "new_mail.html")


def all_sent_mails(request):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.GET.get("close") is not None:
        return redirect("all-sent-mails")

    searched = request.GET.get("searched") if request.GET.get("searched") else ""

    full_url = request.build_absolute_uri()
    if "searched=&submit=" in full_url:
        redirect_url = full_url.replace("?searched=&submit=", '')
        return redirect(redirect_url)

    elif searched:
        mails = Mail.objects.filter(from_user=request.user).filter(
            Q(to_user__username__icontains=searched) |
            Q(title__icontains=searched)
            )
    else:
        mails = Mail.objects.filter(from_user=request.user)

    profile_pictures = []
    for mail in mails:
        user = User.objects.get(username=mail.to_user_inf)
        try:
            avatar = Profile.objects.get(user=user).avatar
        except ObjectDoesNotExist:
            profile = Profile(user=user)
            profile.save()
            avatar = Profile.objects.get(user=user).avatar
        profile_pictures.append(avatar)

    context = mails_settings(request=request, user="to_user_inf", mails=mails)

    return render(request, "sent_mails.html", context=context)


def sent_mail(request, pk):

    if not request.user.is_authenticated:
        return redirect('login') 

    try:
        mail = Mail.objects.get(id=pk)
    except ObjectDoesNotExist:
        return redirect("all-sent-mails")

    if mail.from_user != request.user:
        return redirect("all-sent-mails")

    if request.method == "POST":   
        if request.POST.get("Delete"):
            mail.from_user = None
            mail.save()
        return redirect("all-sent-mails")
        
    receiver = User.objects.get(username=mail.to_user_inf)
    try:
        avatar = Profile.objects.get(user=receiver).avatar
    except ObjectDoesNotExist:
        profile = Profile(user=receiver)
        profile.save()
        avatar = Profile.objects.get(user=receiver).avatar
    
    context = {"mail": mail, "avatar": avatar}
    return render(request, "sent_mail.html", context=context)


def all_received_mails(request):

    if not request.user.is_authenticated:
        return redirect('login')

    if request.GET.get("close") is not None:
        return redirect("all-received-mails")

    full_url = request.build_absolute_uri()
    if "searched=&submit=" in full_url:
        redirect_url = full_url.replace("?searched=&submit=", '')
        return redirect(redirect_url)

    searched = request.GET.get("searched") if request.GET.get("searched") else ""

    if searched.lower() == "all":
        return redirect("all-received-mails")

    elif searched:
        mails = Mail.objects.filter(to_user=request.user).filter(
            Q(from_user__username__icontains=searched) |
            Q(title__icontains=searched)
            )
    else:
        mails = Mail.objects.filter(to_user=request.user)
    
    context = mails_settings(request=request, user="from_user_inf", mails=mails)
    return render(request, "received_mails.html", context=context)


def received_mail(request, pk):
    
    if not request.user.is_authenticated:
        return redirect('login') 
    
    try:
        mail = Mail.objects.get(id=pk)
        if mail.unvisited:
            mail.unvisited = False
            mail.save()
    except ObjectDoesNotExist:
        return redirect("all-received-mails")

    if mail.to_user != request.user:
        return redirect("all-received-mails")
    
    if request.method == "POST": 
        if request.POST.get("Delete"):
            mail.to_user = None
            mail.save()
        return redirect("all-received-mails")
        
    sender = User.objects.get(username=mail.from_user_inf)
    try:
        avatar = Profile.objects.get(user=sender).avatar
    except ObjectDoesNotExist:
        profile = Profile(user=sender)
        profile.save()
        avatar = Profile.objects.get(user=sender).avatar

    context = {"mail": mail, "avatar": avatar}
    return render(request, "received_mail.html", context=context)


def my_profile(request):

    if not request.user.is_authenticated:
        return redirect('login') 

    try:
        my_profile_var = Profile.objects.get(user=request.user)
    except ObjectDoesNotExist:  # another one handler bacause of a superuser which profile will be created by code below
        profile = Profile(user=request.user)
        profile.save()
        my_profile_var = Profile.objects.get(user=request.user)

    sent_messages = Mail.objects.filter(from_user_inf=request.user).count()
    received_messages = Mail.objects.filter(to_user_inf=request.user).count()

    context = {
        "profile": my_profile_var,
        "sent": sent_messages, 
        "received": received_messages,
        "date_joined": my_profile_var.joined
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
# Error handlers
# Error handlers
# Error handlers
# Error handlers


def handler_404(request, exception):
    pass


def handler_500(request):
    pass
