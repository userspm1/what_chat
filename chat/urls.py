# chat/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('',                          views.index,        name='index'),
    path('chat/<str:room_name>/',     views.room,         name='room'),
    path('group/<int:group_id>/',     views.group_room,   name='group_room'),
    path('group/create/',             views.create_group, name='create_group'),
    path('upload/',                   views.upload_file,  name='upload_file'),
    path('signup/',                   views.signup_view,  name='signup'),
    path('login/',                    views.login_view,   name='login'),
    path('logout/',                   views.logout_view,  name='logout'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)