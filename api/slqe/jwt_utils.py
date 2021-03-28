from datetime import datetime

import jwt
from django.conf import settings
from slqe.models import User


def is_verified(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        verify_token = jwt.encode({
            'id': payload['id'],
            'exp': payload['exp']
        }, settings.SECRET_KEY, algorithm='HS256')
        User.objects.get(uid=payload['id'], is_active=True)
        dt = datetime.now()
        if token != verify_token or int(dt.strftime('%s')) > payload['exp']:
            return False
    except User.DoesNotExist:
        return False
    except ValueError:
        return False
    except TypeError:
        return False
    return True


def is_permitted(token, roles):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        user = User.objects.get(uid=payload['id'], is_active=True)

        if user.role.name in roles:
            return True
    except User.DoesNotExist:
        return False
    except ValueError:
        return False
    except TypeError:
        return False
    return False


class JWTAuthentication:
    pass
