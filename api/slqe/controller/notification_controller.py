import logging
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from slqe.service.notification_service import NotificationService
from django.http.response import *

logger = logging.getLogger(__name__)


class NotificationController(APIView):
    parser_classes = (MultiPartParser, FormParser)

    # Notification
    @api_view(['GET', 'POST', 'DELETE'])
    def notification_list(self, user_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        # check authorization
        role = ("ADMIN", "CUSTOMER")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user_access = User.objects.get(id=payload['id'], is_active=True)

            user = User.objects.get(pk=user_id)

            # only owner user can access resources
            if user_access.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        except DecodeError:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            offset, limit = parse_offset_limit(offset, limit)
            notification_service = NotificationService()
            total, notifications = notification_service.get_notifications(limit, offset, user_id)
            notification_serializer = NotificationSerializer(notifications, many=True)
            return JsonResponse({"total": total, "data": notification_serializer.data}, safe=False)
        elif self.method == 'POST':
            notification = JSONParser().parse(self)
            if notification["user"] != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
            notification_serializer = NotificationSerializer(data=notification)

            if notification_serializer.is_valid():
                notification_service = NotificationService()
                notification_service.create_notification(notification_serializer)
                return HttpResponse(status=status.HTTP_201_CREATED)
            return HttpResponse(notification_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @api_view(['DELETE'])
    def notification_delete_all_read(self, user_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        # check authorization
        role = ("ADMIN", "CUSTOMER")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user_access = User.objects.get(id=payload['id'], is_active=True)

            user = User.objects.get(pk=user_id)

            # only owner user can access resources
            if user_access.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        except DecodeError:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        if self.method == 'DELETE':
            notification_service = NotificationService()
            notification_service.delete_all_read_notification(user_id)
        return HttpResponse(status=status.HTTP_204_NO_CONTENT)

    @api_view(['GET', 'PUT'])
    def notification_detail(self, user_id, notification_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        # check authorization
        role = ("ADMIN", "CUSTOMER")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user_access = User.objects.get(id=payload['id'], is_active=True)

            user = User.objects.get(pk=user_id)

            # only owner user can access resources
            if user_access.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        except DecodeError:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            try:
                notification_service = NotificationService()
                notification = notification_service.get_notification_by_id(notification_id, user_id)
                notification_serializer = NotificationSerializer(notification)

                return JsonResponse(notification_serializer.data)
            except Notification.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        elif self.method == 'PUT':
            try:
                request_data = json.loads(self.body)
                is_read = request_data["is_read"]
                is_success = request_data["is_success"]
                notification_service = NotificationService()
                notification = notification_service.get_notification_by_id(notification_id, user_id)
                is_save = False
                if is_read:
                    notification.is_read = True
                    is_save = True
                if is_success is False:
                    notification.is_success = False
                    is_save = True

                if is_save:
                    notification_service.update_notification(notification)

                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except Notification.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    @api_view(['GET'])
    def notification_count_unread(self, user_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        # check authorization
        role = ("ADMIN", "CUSTOMER")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user_access = User.objects.get(id=payload['id'], is_active=True)

            user = User.objects.get(pk=user_id)

            # only owner user can access resources
            if user_access.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)

        except DecodeError:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            notification_service = NotificationService()
            total = notification_service.count_unread(user_id)
            return JsonResponse({"total": total}, safe=False)
