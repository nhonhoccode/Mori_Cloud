import os
from .models import *
from .serializers import *
from rest_framework import status
from django.shortcuts import render
from rest_framework.views import APIView
from mori.settings import STATICFILES_DIRS
from rest_framework.response import Response

def not_found(request, path):
    return render(request, 'err/index.html')

def landing(request):
    return render(request, 'landing/index.html')

def loginUI(request):
    return render(request, 'auth/login/index.html')

def register(request):
    return render(request, 'auth/register/index.html')

def forgot_password(request):
    return render(request, 'auth/forgetpass/index.html')

def adminUI(request):
    return render(request, 'admin/index.html')

def home(request):
    token = request.session.get('token', None)  
    return render(request, 'home/index.html', {'token': token})

def manage_imgs(request):
    return render(request, 'manage_imgs/index.html')

def history_imgs(request):
    return render(request, 'history_imgs/index.html')

def social(request):
    return render(request, 'social/index.html')

def history_imgs(request):
    return render(request, 'history_imgs/index.html')

def imgs(request):
    return render(request, 'imgs/index.html')

def profile(request):
    return render(request, 'profile/index.html')

def trash(request):
    return render(request, 'trash/index.html')


class Objects(APIView):
    def get(self, request): 
        objects_path = STATICFILES_DIRS[0] + "/image/objects" 
        # kiểm tra thư mục objects_path có tồn tại không
        if not os.path.exists(objects_path):
            return Response({"error":"objects not found"}, status=status.HTTP_404_NOT_FOUND)
        objects = os.listdir(objects_path)

        image_objects = [
            {
                'src': f'/static/image/objects/{name}',
                'name': name.replace('.png', '').replace('_', ' ').title()  
            }
            for name in objects
        ]
        return Response({"image_objects":image_objects}, status=status.HTTP_200_OK)
    
class Colors(APIView):
    def get(self, request): 
        objects_path = STATICFILES_DIRS[0] + "/image/color" 
        # kiểm tra thư mục objects_path có tồn tại không
        if not os.path.exists(objects_path):
            return Response({"error":"objects not found"}, status=status.HTTP_404_NOT_FOUND)
        objects = os.listdir(objects_path)

        image_objects = [
            {
                'src': f'/static/image/color/{name}',
                'name': name.replace('.png', '').replace('_', '').title()  
            }
            for name in objects
        ]
        return Response({"image_objects":image_objects}, status=status.HTTP_200_OK)

