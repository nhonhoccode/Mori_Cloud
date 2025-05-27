from django.urls import path
from .templateUI import *

urlpatterns = [    
    # landing
    path("landing", landing),
    # auth
    path("login", loginUI),
    path("register", register),
    path("forgot-password", forgot_password),
    # dashboard
    path("home", home),
    path("imgs", imgs),
    path("trash", trash),
    path("admin", adminUI),
    path("social", social),
    path("profile", profile),
    path("manage-imgs", manage_imgs),
    path("history-imgs", history_imgs),
    # API UI
    path('api/colors/', Colors.as_view(), name='colors'),
    path('api/objects/', Objects.as_view(), name='objects'),
]

