from django.http import HttpResponse
from pastein.models import PasteinContent
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

JSON_TEMPLATE = {
    'status': None,
    'message': None,
    'data': None
}

def set_json_response(data, status=200, message=None):
    json_data = JSON_TEMPLATE.copy()
    json_data['status'] = status
    json_data['data'] = data

    if not message:
        if status == 200:
            json_data['message'] = 'Success'
        elif status == 404:
            json_data['message'] = 'Not found'
        elif status == 401:
            json_data['message'] = 'Unauthorized'
    else:
        json_data['message'] = message

    return json.dumps(json_data)

@csrf_exempt
def update_views(request):
    auth = request.headers.get('Authorization')

    if auth != 'Bearer ' + settings.CRON_API_SECRET:
        return HttpResponse(set_json_response(None, 401), status=401, content_type='application/json')

    data = PasteinContent.persist_hits_to_db()

    return HttpResponse(set_json_response(data, 200, 'Hits updated successfully.'), content_type='application/json')

@csrf_exempt
def clear_expired_pastes(request):
    auth = request.headers.get('Authorization')

    if auth != 'Bearer ' + settings.CRON_API_SECRET:
        return HttpResponse(set_json_response(None, 401), status=401, content_type='application/json')

    data = PasteinContent.clear_expired_pastes()

    return HttpResponse(set_json_response(data, 200, 'Expired pastes cleared successfully.'), content_type='application/json')