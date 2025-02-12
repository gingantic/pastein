from django.http import HttpResponse
from pastein.models import PasteinContent
from django.views.decorators.csrf import csrf_exempt
from api.utils import set_json_response
from api.decorators import require_cron_auth

# Create your views here.
@csrf_exempt
@require_cron_auth
def update_views(request):
    data = PasteinContent.persist_hits_to_db()
    return HttpResponse(set_json_response(data, 200, 'Hits updated successfully.'), content_type='application/json')

@csrf_exempt
@require_cron_auth
def clear_expired_pastes(request):
    data = PasteinContent.clear_expired_pastes()
    return HttpResponse(set_json_response(data, 200, 'Expired pastes cleared successfully.'), content_type='application/json')