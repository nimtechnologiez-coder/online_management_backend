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
