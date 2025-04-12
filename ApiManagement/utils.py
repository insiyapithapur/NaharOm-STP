from .models import ApiStatus

def get_api_status(api_name):
    try:
        return ApiStatus.objects.get(api_name=api_name)
    except ApiStatus.DoesNotExist:
        return None


def is_api_enabled(api_name):
    api_status = get_api_status(api_name)
    return api_status.is_enabled if api_status else False


def get_api_alternative(api_name):
    api_status = get_api_status(api_name)
    return api_status.alternate_api if api_status else False
