from django.shortcuts import redirect
from django.utils.cache import add_never_cache_headers

class RequireRoleChoiceMiddleware:
    """Gate every view for signed-in legacy accounts, including existing sessions."""
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        return self.get_response(request)
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated and request.user.role is None:
            if request.resolver_match.url_name not in {'choose_role', 'logout'}:
                response = redirect('choose_role')
                add_never_cache_headers(response)
                return response
