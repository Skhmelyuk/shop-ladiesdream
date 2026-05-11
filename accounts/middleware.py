from django.shortcuts import redirect
from django.urls import reverse


class AdminAccessRedirectMiddleware:
    """
    Перенаправляє неавторизованих або не-staff користувачів зі сторінок /admin/.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            user = request.user

            if not user.is_authenticated or not user.is_staff:
                if request.path != reverse('admin:login'):
                    return redirect('main:product-list')

        return self.get_response(request)
