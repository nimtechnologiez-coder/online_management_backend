from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers

class NoCacheMiddleware:
    """
    Security Middleware to prevent client-side browser caching for all responses.
    Ensures clicking the browser 'Back' button after logging out forces a fresh server request,
    preventing unauthorized users from viewing cached admin pages.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        add_never_cache_headers(response)
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response


class AdminRequiredMiddleware:
    """
    Middleware ensuring:
    1. Authenticated admins opening login pages ('/', '/admin/login/') are redirected directly to Admin Dashboard.
    2. Unauthenticated users or expired sessions accessing protected Admin pages are redirected to Login.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info.rstrip('/')

        # 1. Redirect authenticated admins from login page directly to dashboard
        if path in ['', '/admin/login']:
            if request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
                return redirect('dashboard')

        # 2. Protected admin section routes
        protected_prefixes = (
            '/dashboard', '/colleges', '/departments', '/hods', '/principals',
            '/students', '/videos', '/analytics', '/reports', '/users',
            '/settings', '/profile'
        )

        public_api_prefixes = (
            '/student/signup', '/api/student/', '/api/get-principal-by-college', '/api/get-colleges'
        )

        is_public_api = any(path.startswith(prefix) for prefix in public_api_prefixes)
        is_protected = any(path.startswith(prefix) for prefix in protected_prefixes) and not is_public_api

        if is_protected:
            if not request.user.is_authenticated or not (request.user.is_superuser or request.user.is_staff):
                return redirect('admin_login')

        return self.get_response(request)
