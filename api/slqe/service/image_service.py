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


def get_image(image_id, user):
    status_code = 200
    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        status_code = 404
        return None, status_code
    if image.user.id != user.id:
        status_code = 403
        return None, status_code
    return image, status_code


def delete_image(image_id, user):
    status_code = 204
    try:
        image = Image.objects.get(id=image_id)
    except Image.DoesNotExist:
        status_code = 404
        return status_code
    if image.user.id != user.id:
        status_code = 403
        return status_code
        # config s3 amazon
    s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
    bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
    obj = bucket.Object(image.url)
    obj.delete()
    image.delete()
    return status_code


def get_images(user_id, limit, offset):
    total_image = Image.objects.filter(user=user_id).order_by('-date_time').count()
    offset, limit = parse_offset_limit(offset, limit)
    images = Image.objects.filter(user=user_id).order_by('-date_time')[offset:offset + limit]
    return total_image, images


def solve_equation(file_obj, user, self):
    status_code = 201
    try:
        image = PIL.Image.open(file_obj)
    except (MultiValueDictKeyError, UnidentifiedImageError):
        status_code = 400
        return None, status_code
    now = datetime.now()
    url = ""
    parsed_array = asarray(image)
    parsed_array = cv2.cvtColor(parsed_array, cv2.COLOR_RGB2BGR)
    valid, message, expression, latex, roots = algorithm.process(parsed_array)

    if self.POST and self.POST['save'] and self.POST['save'] == '1':
        filename = file_obj.name
        file_obj.seek(0, 0)
        s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        bucket.put_object(Key=filename + "_" + str(now), Body=file_obj)
        url = "https://s3-%s.amazonaws.com/%s/%s" % (
            settings.AWS_LOCATION, settings.AWS_STORAGE_BUCKET_NAME, filename)
        image_model = Image.create(user=user, url=url, date_time=now, expression=expression, latex=latex,
                                   roots=roots, success=valid, message=message)
        image_model.save()
    else:
        image_model = Image.create(user=user, url=url, date_time=now, expression=expression, latex=latex,
                                   roots=roots, success=valid, message=message)

    return image_model, status_code


class ImageService:
    pass
