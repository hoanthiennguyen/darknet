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
from slqe.jwt_utils import *
from slqe.serializers import *
from slqe.utils import parse_offset_limit
from pathlib import Path

logger = logging.getLogger(__name__)


class SlqeApi(APIView):
    parser_classes = (MultiPartParser, FormParser,)

    @api_view(['GET', 'POST'])
    def user_list(self):
        if self.method == 'GET':
            # get token from header
            token = self.META.get('HTTP_AUTHORIZATION')
            # check authentication
            flag_verify = is_verified(token=token)
            if not flag_verify:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

            # check authorization
            role = ("ADMIN")
            flag_permission = is_permitted(token, role)
            if not flag_permission:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
            name = self.GET.get('name')
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            offset, limit = parse_offset_limit(offset, limit)
            if name:
                total_user = User.objects.filter(name__icontains=name, role=Role.customer_role()).count()
                users = User.objects.filter(name__icontains=name, role=Role.customer_role())[offset:offset + limit]
            else:
                total_user = User.objects.filter(role=Role.customer_role()).count()
                users = User.objects.filter(role=Role.customer_role())[offset:offset + limit]
            user_serializer = UserSerializer(users, many=True)
            return JsonResponse({"total": total_user, "data": user_serializer.data}, safe=False)
        elif self.method == 'POST':
            user_data = JSONParser().parse(self)
            try:
                user_firebase = auth.get_user(user_data['uid'])
                users = User.objects.filter(uid=user_firebase.uid)
                if users:
                    user = users[0]
                    if user.is_active:
                        return JsonResponse({"user": UserSerializer(user).data, "token": user.token},
                                            status=status.HTTP_200_OK, safe=False)
                    else:
                        return HttpResponseBadRequest("User inactive")
                else:
                    user = User.create(email=user_firebase.email, uid=user_firebase.uid, password=None,
                                       phone=user_firebase.phone_number, avatar_url=user_firebase.photo_url,
                                       name=user_firebase.display_name, role=Role.create(role_id=1, name="USER"))
                    user.save()
                    return JsonResponse({"user": UserSerializer(user).data, "token": user.token},
                                        status=status.HTTP_201_CREATED, safe=False)
            except UserNotFoundError:
                return HttpResponseBadRequest("User not found")
            except (ValueError, KeyError):
                return HttpResponseBadRequest("Error when retrieve user info: invalid uid")
            except FirebaseError:
                return HttpResponseServerError("Cannot retrieve user info from firebase")

    @api_view(['GET', 'PUT', 'DELETE'])
    def user_detail(self, user_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            try:
                # check authorization
                role = ("CUSTOMER", "ADMIN")
                flag_permission = is_permitted(token, role)
                if not flag_permission:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)

                payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
                user_access = User.objects.get(id=payload['id'], is_active=True)

                user = User.objects.get(pk=user_id)
                user_serializer = UserSerializer(user)

                # only owner user can access resources
                if user_access.role.name == "CUSTOMER":
                    if user_access.id != user.id:
                        return HttpResponse(status=status.HTTP_403_FORBIDDEN)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except DecodeError:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
            return JsonResponse(user_serializer.data, safe=False)
        elif self.method == 'PUT':
            try:
                # check authorization
                role = ("ADMIN")
                flag_permission = is_permitted(token, role)
                if not flag_permission:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)

                user = User.objects.get(pk=user_id)
                request_data = JSONParser().parse(self)
                user.is_active = request_data['is_active']
                user.save()
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except (ValidationError, KeyError):
                return HttpResponseBadRequest()
        elif self.method == 'DELETE':
            try:
                # check authorization
                role = ("ADMIN")
                flag_permission = is_permitted(token, role)
                if not flag_permission:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)

                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            user.is_active = False
            user.save()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

    # ------- Image view -------------------

    @api_view(['POST'])
    def process_image(self):
        print(os.getcwd())
        file_obj = self.FILES['file']
        image = PIL.Image.open(file_obj)

        parsed_array = asarray(image)
        parsed_array = cv2.cvtColor(parsed_array, cv2.COLOR_RGB2BGR)

        valid, message, expression, latex, roots = algorithm.process(parsed_array)

        return JsonResponse({"success": valid, "message": message, "expression": expression,
                             "latex": latex, "roots": roots}, status=status.HTTP_200_OK)

    @api_view(['GET', 'DELETE'])
    def images_detail(self, user_id, image_id):
        try:
            # get token from header
            token = self.META.get('HTTP_AUTHORIZATION')
            # check authentication
            flag_verify = is_verified(token=token)
            if not flag_verify:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

            # check authorization
            role = ("CUSTOMER")
            flag_permission = is_permitted(token, role)
            if not flag_permission:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)

            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return JsonResponse({'message': 'The image does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if image.user.id != user.id:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        if self.method == 'GET':
            image_serializer = ImageSerializer(image)
            return JsonResponse(image_serializer.data, safe=False)
        elif self.method == 'DELETE':
            # config s3 amazon
            s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
            obj = bucket.Object(image.url)
            obj.delete()
            image.delete()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)

    @api_view(['GET', 'POST'])
    def user_images(self, user_id):
        try:
            # get token from header
            token = self.META.get('HTTP_AUTHORIZATION')
            # check authentication
            flag_verify = is_verified(token=token)
            if not flag_verify:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

            # check authorization
            role = ("CUSTOMER")
            flag_permission = is_permitted(token, role)
            if not flag_permission:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)

            payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
            user_access = User.objects.get(id=payload['id'], is_active=True)

            user = User.objects.get(id=user_id, is_active=True)

            if user_access.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except DecodeError:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            total_image = Image.objects.filter(user=user_id).order_by('-date_time').count()
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            offset, limit = parse_offset_limit(offset, limit)
            images = Image.objects.filter(user=user_id).order_by('-date_time')[offset:offset + limit]
            image_serializer = ImageSerializer(images, many=True)
            return JsonResponse({"total": total_image, "data": image_serializer.data}, safe=False)
        elif self.method == 'POST':
            try:
                file_obj = self.FILES['file']
                image = PIL.Image.open(file_obj)
            except (MultiValueDictKeyError, UnidentifiedImageError):
                return JsonResponse({"message": "An application require a image to recognize"},
                                    status=status.HTTP_400_BAD_REQUEST)
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
                image_serializer = ImageSerializer(image_model)
            else:
                image_model = Image.create(user=user, url=url, date_time=now, expression=expression, latex=latex,
                                           roots=roots, success=valid, message=message)
                image_serializer = ImageSerializer(image_model)

            return JsonResponse(image_serializer.data, status=status.HTTP_201_CREATED)

    # class version
    @api_view(['GET', 'POST'])
    def class_list(self):
        if self.method == 'GET':
            # get token from header
            token = self.META.get('HTTP_AUTHORIZATION')
            # check authentication
            flag_verify = is_verified(token=token)
            if not flag_verify:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

            # check authorization
            role = ("ADMIN")
            flag_permission = is_permitted(token, role)
            if not flag_permission:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)

            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            offset, limit = parse_offset_limit(offset, limit)
            version = ClassVersion.objects.all().order_by('-created_date')
            total = len(version)
            version = version[offset:offset + limit]
            class_serializer = ClassSerializer(version, many=True)
            return JsonResponse({"total": total, "data": class_serializer.data}, safe=False)
        elif self.method == 'POST':
            version_data = JSONParser().parse(self)

            class_serializer = ClassSerializer(data=version_data)
            if class_serializer.is_valid():
                class_serializer.save()
                return JsonResponse(class_serializer.data, status=status.HTTP_201_CREATED, safe=False)

            return JsonResponse(class_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @api_view(['GET', 'PUT'])
    def class_detail(self, class_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        # check authorization
        role = ("ADMIN")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        if self.method == "GET":
            try:
                version = ClassVersion.objects.get(pk=class_id)
                class_serializer = ClassSerializer(version)
                return JsonResponse(class_serializer.data, safe=False)
            except ClassVersion.DoesNotExist:
                return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        elif self.method == 'PUT':
            try:
                version = ClassVersion.objects.get(pk=class_id)
                request_data = json.loads(self.body)
                commit_hash = request_data['commit_hash']
                if commit_hash is not None or len(commit_hash) > 0:
                    version.commit_hash
                    version.save()
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except (ValidationError, KeyError):
                return HttpResponseBadRequest()

    @api_view(['GET'])
    def class_get_last_version(self):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        # check authorization
        role = ("ADMIN")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)

        if self.method == 'GET':
            version = ClassVersion.objects.order_by('-created_date').first()
            if version:
                class_serializer = ClassSerializer(version)
                return JsonResponse(class_serializer.data, safe=False)
            return HttpResponse(status=status.HTTP_200_OK)

    # weight version
    @api_view(['GET', 'POST'])
    def weight_list(self, class_id):

        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        # check authorization
        role = ("ADMIN")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            class_version = ClassVersion.objects.get(pk=class_id)
        except ClassVersion.DoesNotExist:
            return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            offset, limit = parse_offset_limit(offset, limit)
            versions = WeightVersion.objects.filter(class_version=class_id).order_by('-created_date')
            total = len(versions)
            versions = versions[offset:offset + limit]
            weight_serializer = WeightSerializer(versions, many=True)
            return JsonResponse({"total": total, "data": weight_serializer.data}, safe=False)
        elif self.method == 'POST':
            dt = datetime.now()
            file_obj = self.FILES['file']
            if file_obj:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
                script_dir = Path(os.path.dirname(__file__))
                parent = script_dir.parent
                save_path = os.path.join(parent, "weights", payload["id"], str(int(time.mktime(dt.timetuple()))))
                file_name = file_obj.name
                Path(f"{save_path}").mkdir(parents=True, exist_ok=True)
                completeName = os.path.join(save_path, file_name)

                # open read and write the file into the server
                open(completeName, 'wb').write(file_obj.file.read())

                version = WeightVersion.objects.filter(class_version=class_id).order_by('-created_date').first()
                if version:
                    version = int(version.version) + 1
                else:
                    version = 1
                weight = WeightVersion.create(created_date=dt, class_version=class_version, version=version,
                                              url=os.path.relpath(completeName))
                weight.save()
                return HttpResponse(status=status.HTTP_201_CREATED)
            else:
                return JsonResponse({"message": "Please select weight to create."},
                                    status=status.HTTP_400_BAD_REQUEST)

    @api_view(['GET', 'PUT'])
    def weight_detail(self, class_id, weight_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        # check authorization
        role = ("ADMIN")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            ClassVersion.objects.get(pk=class_id)
        except ClassVersion.DoesNotExist:
            return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            try:
                version = WeightVersion.objects.get(pk=weight_id, class_version=class_id)
                weight_serializer = WeightSerializer(version)
                return JsonResponse(weight_serializer.data, safe=False)
            except WeightVersion.DoesNotExist:
                return JsonResponse({'message': 'The weight version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        elif self.method == 'PUT':
            try:
                version = WeightVersion.objects.get(pk=weight_id)
                request_data = json.loads(self.body)
                url = request_data['url']
                is_active = request_data['is_active']
                is_save = False
                if url is not None and len(url) > 0:
                    version.url = url
                    is_save = True

                if is_active:
                    version.is_active = is_active
                    current_version = WeightVersion.objects.filter(is_active=True).first()
                    if current_version:
                        current_version.is_active = False
                        current_version.save()
                    is_save = True

                if is_save:
                    version.save()

                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except WeightVersion.DoesNotExist:
                return JsonResponse({'message': 'The weight version does not exist'}, status=status.HTTP_404_NOT_FOUND)

    @api_view(['GET'])
    def weight_get_last_version(self, class_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        # check authorization
        role = ("ADMIN")
        flag_permission = is_permitted(token, role)
        if not flag_permission:
            return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        try:
            ClassVersion.objects.get(pk=class_id)
        except ClassVersion.DoesNotExist:
            return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if self.method == 'GET':
            version = WeightVersion.objects.filter(class_version=class_id).order_by('-created_date').first()
            if version:
                weight_serializer = WeightSerializer(version)
                return JsonResponse(weight_serializer.data, safe=False)
            return HttpResponse(status=status.HTTP_200_OK)

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
            notifications = Notification.objects.filter(user=user_id, is_delete=False).order_by('-created_date')
            total = len(notifications)
            notifications = notifications[offset:offset + limit]
            notification_serializer = NotificationSerializer(notifications, many=True)
            return JsonResponse({"total": total, "data": notification_serializer.data}, safe=False)
        elif self.method == 'POST':
            notification = JSONParser().parse(self)
            if notification["user"] != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
            notification_serializer = NotificationSerializer(data=notification)

            if notification_serializer.is_valid():
                notification_serializer.save()
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
            notifications = Notification.objects.filter(is_read=True, user=user_id).update(is_delete=True)
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
                notification = Notification.objects.get(pk=notification_id, user=user_id)
                notification_serializer = NotificationSerializer(notification)

                return JsonResponse(notification_serializer.data)
            except Notification.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        elif self.method == 'PUT':
            try:
                notification = Notification.objects.get(pk=notification_id, user=user_id)
                notification.is_read = True
                notification.save()

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
            notifications = Notification.objects.filter(user=user_id, is_read=False)
            total = len(notifications)
            return JsonResponse({"total": total}, safe=False)
