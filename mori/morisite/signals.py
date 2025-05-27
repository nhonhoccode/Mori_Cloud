from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Album, Trash, Like, Avatar
from knox.models import AuthToken
from allauth.account.signals import user_logged_in

@receiver(post_save, sender=User)
def create_user_album(sender, instance, created, **kwargs):
    if created:
        Album.objects.create(user=instance, title='Tất cả', is_main=True)
        Avatar.objects.create(user=instance)

@receiver(user_logged_in)
def create_knox_token(sender, request, user, **kwargs):
    token = AuthToken.objects.create(user=user)
    print(f"User logged in: {user}, token: {token[1]}")
    request.session['token'] = token[1] 
    return token