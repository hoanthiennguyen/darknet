from datetime import datetime, timedelta

import jwt
from django.conf import settings
from slqe.models import User


def verify(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        verify_token = jwt.encode({
            'id': payload['id'],
            'exp': payload['exp']
        }, settings.SECRET_KEY, algorithm='HS256')
        User.objects.get(uid=payload['id'], is_active=True)
        dt = datetime.now() + timedelta(days=360)
        if token != verify_token or int(dt.strftime('%s')) < int(payload['exp']):
            return False
    except:
        return False
    return True


class JWTAuthentication:
    pass