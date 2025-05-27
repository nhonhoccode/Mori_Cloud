from django.http import JsonResponse
from .models import User
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from django.shortcuts import render, redirect

def profile(request):
    return render(request, 'profile.html', {"user": request.user})

def custom_login_view(request):
    return render(request, "auth/login/index.html") 

def home_page(request):
    token = request.session.get('token', None)  
    return render(request, 'base/index.html', {'token': token})

def redirect_landing(request):
    return redirect('/page/landing')    

class ForgotPasswordView(APIView):
    """
    Custom APIView để gửi email reset password bằng send_mail().
    """
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        print(f"📩 Nhận yêu cầu reset password cho: {email}")
        if not email:
            return JsonResponse({'error': 'Email là bắt buộc!'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Email này không tồn tại trong hệ thống!'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_email == True:
            return JsonResponse({'error': 'Email này chỉ đăng nhập bằng gmail không hổ trợ lấy lại mật khẩu!'}, status=status.HTTP_400_BAD_REQUEST) 
        
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = f"http://127.0.0.1:8000/reset/{uid}/{token}/"

        subject = "Đặt lại mật khẩu của bạn"
        message = f"""
        Xin chào {user.email},

        Bạn đã yêu cầu đặt lại mật khẩu. Nhấn vào đường link bên dưới để tiếp tục:

        {reset_link}

        Nếu bạn không yêu cầu, vui lòng bỏ qua email này.

        Trân trọng,
        Đội ngũ hỗ trợ MORI
        """
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            print("✅ Email gửi thành công!")
            return JsonResponse({'message': 'Email đặt lại mật khẩu đã được gửi!'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"❌ Lỗi gửi email: {e}")
            return JsonResponse({'error': 'Gửi email thất bại!'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        