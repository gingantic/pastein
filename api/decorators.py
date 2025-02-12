from django.http import HttpResponse
from api.utils import set_json_response
from django.conf import settings

def require_cron_auth(view_func):
    def wrapper(request, *args, **kwargs):
        auth = request.headers.get('Authorization')

        if auth != 'Bearer ' + settings.CRON_API_SECRET:
            return HttpResponse(set_json_response(None, 401), status=401, content_type='application/json')
        return view_func(request, *args, **kwargs)
    return wrapper