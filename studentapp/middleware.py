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


from django.core.cache import cache
from django.http import JsonResponse

class SimpleRateLimitMiddleware:
    """
    Cache-based rate limiting middleware.
    Limits request rates per IP:
    - Sensitive endpoints (Login, OTP Send): 5 requests per minute.
    - Other API endpoints: 60 requests per minute.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/'):
            # Get IP
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip:
                ip = ip.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')

            # Identify tight limit endpoints
            tight_endpoints = [
                '/api/student/login', '/api/student/login/',
                '/api/hod/login', '/api/hod/login/',
                '/api/principal/login', '/api/principal/login/',
                '/api/student/send-otp', '/api/student/send-otp/',
                '/api/student/forgot-password/send-otp', '/api/student/forgot-password/send-otp/',
            ]
            
            is_tight = any(request.path.startswith(endpoint) for endpoint in tight_endpoints)
            limit = 5 if is_tight else 60
            period = 60  # 1 minute

            cache_key = f"ratelimit:{ip}:{request.path}"
            request_count = cache.get(cache_key, 0)

            if request_count >= limit:
                return JsonResponse({
                    "status": "error",
                    "message": "Too many requests. Please try again later."
                }, status=429)

            cache.set(cache_key, request_count + 1, period)

        return self.get_response(request)
