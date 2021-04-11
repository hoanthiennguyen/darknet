from datetime import datetime

import jwt
from django.conf import settings
from jwt import DecodeError
from slqe.models import User
import time

def is_verified(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        verify_token = jwt.encode({
            'id': payload['id'],
            'exp': payload['exp']
        }, settings.SECRET_KEY, algorithm='HS256')
        User.objects.get(id=payload['id'], is_active=True)
        dt = datetime.now()
        expired = time.mktime(dt.timetuple())
        if token != verify_token or int(expired) > payload['exp']:
            return False
    except User.DoesNotExist:
        return False
    except ValueError:
        return False
    except TypeError:
        return False
    except DecodeError:
        return False
    return True


def is_permitted(token, roles):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
        user = User.objects.get(id=payload['id'], is_active=True)

        if user.role.name in roles:
            return True
    except User.DoesNotExist:
        return False
    except ValueError:
        return False
    except TypeError:
        return False
    except DecodeError:
        return False
    return False


class JWTAuthentication:
    pass
