import logging
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit

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
