import logging
from datetime import datetime

import PIL.Image
import boto3
import cv2
from PIL import UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.http.response import *
from django.utils.datastructures import MultiValueDictKeyError
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
from firebase_admin.exceptions import FirebaseError
from numpy import asarray
from processor import algorithm
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from pathlib import Path

logger = logging.getLogger(__name__)


def get_users(name, limit, offset):
    offset, limit = parse_offset_limit(offset, limit)
    if name:
        total_user = User.objects.filter(name__icontains=name, role=Role.customer_role()).count()
        users = User.objects.filter(name__icontains=name, role=Role.customer_role())[offset:offset + limit]
    else:
        total_user = User.objects.filter(role=Role.customer_role()).count()
        users = User.objects.filter(role=Role.customer_role())[offset:offset + limit]

    return total_user, users


def get_user(user_id):
    return User.objects.get(pk=user_id)


def update_user(user_id, request_data):
    # check authorization
    user = User.objects.get(pk=user_id)
    user.is_active = request_data['is_active']
    user.save()


def delete_user(user_id):
    user = User.objects.get(pk=user_id)
    user.is_active = False
    user.save()


def login(uid):
    try:
        user_firebase = auth.get_user(uid)
        users = User.objects.filter(uid=user_firebase.uid)
        is_active = False
        if users:
            user = users[0]
            if user.is_active:
                is_active = True

            else:
                return HttpResponseBadRequest("User inactive")
        else:
            user = User.create(email=user_firebase.email, uid=user_firebase.uid, password=None,
                               phone=user_firebase.phone_number, avatar_url=user_firebase.photo_url,
                               name=user_firebase.display_name, role=Role.create(role_id=1, name="USER"))
            user.save()
        return user, is_active
    except UserNotFoundError:
        return HttpResponseBadRequest("User not found")
    except (ValueError, KeyError):
        return HttpResponseBadRequest("Error when retrieve user info: invalid uid")
    except FirebaseError:
        return HttpResponseServerError("Cannot retrieve user info from firebase")


def get_user_active(user_id):
    user = User.objects.get(pk=user_id, is_active=True)
    return user



class UserService:
    pass
