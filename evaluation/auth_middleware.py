from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'require_password_change', False):
            allowed_paths = {
                reverse('initial_password_change'),
                reverse('logout'),
            }
            if request.path not in allowed_paths and not request.path.startswith('/admin/'):
                return redirect('initial_password_change')
        return self.get_response(request)
