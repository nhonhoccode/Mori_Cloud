from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from knox.models import AuthToken

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):

    def pre_social_login(self, request, sociallogin):
        """
        ✅ Kiểm tra user trước khi hoàn tất đăng nhập Google
        ✅ Tránh lỗi `AssertionError` khi user đã có email trong database
        """
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return  

        try:
            existing_user = User.objects.get(email=email)
            sociallogin.user = existing_user  

            if not EmailAddress.objects.filter(user=existing_user, email=email).exists():
                EmailAddress.objects.create(user=existing_user, email=email, verified=True, primary=True)

        except User.DoesNotExist:
            user_new = User.objects.create(email=email, is_email=True,name=email.split("@")[0])
            user_new.save()

            sociallogin.user = user_new

            EmailAddress.objects.create(user=user_new, email=email, verified=True, primary=True)

        if AuthToken.objects.filter(user=sociallogin.user).exists():
            AuthToken.objects.filter(user=sociallogin.user).delete()

        _, token = AuthToken.objects.create(sociallogin.user)
        request.session['token'] = token

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        email = data.get("email")
        if email:
            user.email = email
            user.name = email.split("@")[0]
            user.is_email = True
        return user
