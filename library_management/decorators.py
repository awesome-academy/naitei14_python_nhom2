from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from accounts.models import MemberProfile

def admin_required(view_func):
    def check(user):
        return(
            user.is_authenticated and
            user.profile.role == MemberProfile.Role.ADMIN
        )
    decorated_view_func = user_passes_test(
        check,
        login_url="login"
    )(view_func)
    return decorated_view_func
