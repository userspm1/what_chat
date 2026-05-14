# chat/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user      = models.OneToOneField(User, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}"

class Group(models.Model):
    name       = models.CharField(max_length=255)
    members    = models.ManyToManyField(User, related_name='chat_groups')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    MESSAGE_TYPES = (
        ('text',  'Text'),
        ('image', 'Image'),
        ('file',  'File'),
    )
    room_name    = models.CharField(max_length=255)
    sender       = models.ForeignKey(User, on_delete=models.CASCADE)
    content      = models.TextField(blank=True)
    file_url     = models.TextField(blank=True, null=True)   # ← ADDED
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    timestamp    = models.DateTimeField(auto_now_add=True)
    is_read      = models.BooleanField(default=False)
    deleted_for_everyone = models.BooleanField(default=False)  # ← ADDED

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"
    

class Formdata(models.Model):
    name=models.CharField(max_length=20)
    age=models.IntegerField()
    