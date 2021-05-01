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
# from processor import algorithm
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationService:
    pass

    def get_notifications(self, limit, offset, user_id):
        offset, limit = parse_offset_limit(offset, limit)
        notifications = Notification.objects.filter(user=user_id, is_delete=False).order_by('-created_date')
        total = len(notifications)
        notifications = notifications[offset:offset + limit]
        return total, notifications

    def create_notification(self, notification_serializer):
        notification_serializer.save()
        return notification_serializer

    def get_notification_by_id(self, notification_id, user_id):
        notification = Notification.objects.get(pk=notification_id, user=user_id)
        return notification

    def count_unread(self, user_id):
        notifications = Notification.objects.filter(user=user_id, is_read=False)
        total = len(notifications)
        return total

    def update_notification(self, notification_serializer):
        notification_serializer.save()
        return notification_serializer

    def delete_all_read_notification(self, user_id):
        Notification.objects.filter(is_read=True, user=user_id).update(is_delete=True)
