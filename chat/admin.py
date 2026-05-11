# chat/admin.py
from django.contrib import admin
from .models import Message, UserProfile, Group

admin.site.register(Message)
admin.site.register(UserProfile)
admin.site.register(Group)