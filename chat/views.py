# chat/views.py
import os
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import SignUpForm
from .models import Message, UserProfile, Group

@login_required
def index(request):
    users = User.objects.exclude(id=request.user.id)
    contacts = []
    for u in users:
        room = '_'.join(sorted([str(request.user.id), str(u.id)]))
        last = Message.objects.filter(room_name=room).last()
        profile = UserProfile.objects.filter(user=u).first()
        contacts.append({
            'user':         u,
            'room':         room,
            'last_message': last,
            'is_online':    profile.is_online if profile else False,
        })
    groups = Group.objects.filter(members=request.user)
    return render(request, 'chat/index.html', {'contacts': contacts, 'groups': groups})

@login_required
def room(request, room_name):
    ids        = room_name.split('_')
    other_id   = ids[1] if str(request.user.id) == ids[0] else ids[0]
    other_user = User.objects.get(id=other_id)
    messages   = Message.objects.filter(room_name=room_name)
    profile    = UserProfile.objects.filter(user=other_user).first()
    Message.objects.filter(room_name=room_name, is_read=False).exclude(sender=request.user).update(is_read=True)
    return render(request, 'chat/room.html', {
        'room_name':    room_name,
        'other_user':   other_user,
        'messages':     messages,
        'current_user': request.user,
        'is_online':    profile.is_online if profile else False,
    })

@login_required
def group_room(request, group_id):
    group    = Group.objects.get(id=group_id)
    messages = Message.objects.filter(room_name=f'group_{group_id}')
    return render(request, 'chat/group_room.html', {
        'group':        group,
        'messages':     messages,
        'current_user': request.user,
        'room_name':    f'group_{group_id}',
    })

@login_required
def create_group(request):
    if request.method == 'POST':
        name    = request.POST.get('name')
        members = request.POST.getlist('members')
        group   = Group.objects.create(name=name, created_by=request.user)
        group.members.add(request.user)
        for mid in members:
            group.members.add(User.objects.get(id=mid))
        return redirect('group_room', group_id=group.id)
    users = User.objects.exclude(id=request.user.id)
    return render(request, 'chat/create_group.html', {'users': users})

@login_required
@csrf_exempt
def upload_file(request):
    if request.method == 'POST' and request.FILES.get('file'):
        f        = request.FILES['file']
        path     = f'media/uploads/{f.name}'
        os.makedirs('media/uploads', exist_ok=True)
        with open(path, 'wb+') as dest:
            for chunk in f.chunks():
                dest.write(chunk)
        return JsonResponse({'url': f'/media/uploads/{f.name}', 'name': f.name, 'type': f.content_type})
    return JsonResponse({'error': 'No file'}, status=400)

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'chat/signup.html', {'form': form})

def login_view(request):
    error = ''
    if request.method == 'POST':
        user = authenticate(username=request.POST['username'], password=request.POST['password'])
        if user:
            login(request, user)
            return redirect('index')
        error = 'Invalid username or password'
    return render(request, 'chat/login.html', {'error': error})

def logout_view(request):
    logout(request)
    return redirect('login')











