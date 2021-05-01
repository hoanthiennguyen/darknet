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
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from pathlib import Path

logger = logging.getLogger(__name__)


def get_classes(limit, offset, version_name):
    offset, limit = parse_offset_limit(offset, limit)
    version = ClassVersion.objects.filter(version__icontains=version_name).order_by('-created_date')
    total = len(version)
    version = version[offset:offset + limit]
    return total, version


def create_class(class_serializer):
    class_serializer.save()
    return class_serializer


def get_class_by_id(class_id):
    image = ClassVersion.objects.get(pk=class_id)
    return image


def class_get_last_version():
    version = ClassVersion.objects.order_by('-created_date').first()
    return version

class ClassVersionService:
    pass
