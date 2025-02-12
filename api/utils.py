import json

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