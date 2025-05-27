from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        if not name:
            raise ValueError('The given name must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, name, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id_user = models.AutoField(primary_key=True) 
    name = models.CharField(max_length=255, blank=False)
    email = models.EmailField(unique=True, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_email = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['name']

class Photo(models.Model):
    id_photo = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)    
    caption = models.TextField(blank=True)
    tags = models.TextField(blank=True)
    colors = models.TextField(blank=True)
    objects_photo = models.TextField(blank=True)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to='photo/', blank=False, null=True)
    is_favorited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    like_count = models.PositiveIntegerField(default=0)
    album = models.ForeignKey('Album', on_delete=models.CASCADE, related_name='photo_album', blank=False, default=None, null=False)
    
    faiss_id = models.IntegerField(blank=True, null=True) 
    faiss_id_public = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return 'Photo '+ str(self.id_photo)
    
    def increate_like(self):
        self.like_count += 1
        self.save()
    
    def decrease_like(self):
        self.like_count -= 1
        self.save()
    
    def move_to_trash(self):
        self.is_deleted = True
        self.save()
        Trash.objects.create(photo=self, album=self.album)

class Album(models.Model):
    id_album = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255, blank=False, default='No title')
    description = models.TextField(blank=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='album_user', blank=False, default=None, null=False)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title + str(self.id_album)
    
    class Meta:
        ordering = ['id_album']

class Trash(models.Model):
    id_trash = models.AutoField(primary_key=True)
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE, related_name='trash_photo', blank=False, default=None, null=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='trash_user', blank=False, default=None)
    deleted_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id_trash']

    def __str__(self):
        return 'trash' + str(self.id_trash)

class Favorite(models.Model):
    id_favorite = models.AutoField(primary_key=True) 
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE, related_name='favorite_photo', blank=False, default=None, null=False)
    note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['id_favorite']
    
    def __str__(self):
        return 'favorite' + str(self.id_favorite)
    
class Search_history(models.Model):
    id_search_history = models.AutoField(primary_key=True)
    search_query = models.CharField(max_length=255, blank=False)
    search_type = models.CharField(max_length=255, blank=True, default='no data')
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='search_user', blank=False, default=None, null=False)
    search_date = models.DateTimeField(auto_now_add=True)

    liked_images = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['search_type']

    def __str__(self):
        return self.search_query  + str(self.id_search_history)

class Like(models.Model):
    id_like = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='like_user', blank=False,  null=False)
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE, related_name='like_photo', blank=False, default=None, null=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id_like']
    
    def __str__(self):
        return 'like' + str(self.id_like)  + ' photo' + ' user' + str(self.user.name)
    
class Avatar(models.Model):
    id_avatar = models.AutoField(primary_key=True)
    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name='avatar_user', blank=False, default=None, null=False)
    avatar = models.ImageField(upload_to='avatar/', blank=True, null=True, default='avatar/default_image/default.jpg')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id_avatar']

    def __str__(self):
        return 'Avatar ' + str(self.id_avatar) + ' - user ' + str(self.user.id_user)

class Comment(models.Model):
    id_comment = models.AutoField(primary_key=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='comment_user', blank=False, default=None, null=False)
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE, related_name='comment_photo', blank=False, default=None, null=False)
    like_count = models.PositiveIntegerField(default=0)
    content = models.TextField(blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    liked_by = models.JSONField(default=list, blank=True)

    def increase_like(self, user):
        if user.id_user not in self.liked_by:
            self.liked_by.append(user.id_user)
            self.like_count += 1
            self.save()

    def decrease_like(self, user):
        if user.id_user in self.liked_by:
            self.liked_by.remove(user.id_user)
            self.like_count -= 1
            self.save()

    def is_liked_by_user(self, user):
        return user.id_user in self.liked_by
    
    def __str__(self):
        return 'Comment: ' + str(f'{self.id_comment}') + '- user id:' + str(f"{self.user.id_user}") 
    
    class Meta:
        ordering = ['id_comment']

class Notification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ('like_photo', 'Like Photo'),
        ('like_comment', 'Like Comment'),
        ('comment_photo', 'Comment Photo'),
        ('reply_comment', 'Reply Comment'),
    ]

    id_notification = models.AutoField(primary_key=True)
    recipient = models.ForeignKey('User', on_delete=models.CASCADE, related_name='notifications', blank=False)
    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_notifications', blank=False)
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPE_CHOICES)
    photo = models.ForeignKey('Photo', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.name} -> {self.recipient.name}: {self.notif_type}'
