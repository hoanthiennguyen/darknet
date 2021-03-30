import logging
from datetime import datetime

import PIL.Image
import boto3
import cv2
from PIL import UnidentifiedImageError
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
from slqe.serializers import *
import logging
from slqe.utils import parse_offset_limit

from slqe.jwt_utils import *

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
                users = User.objects.filter(name__icontains=name, role=Role.customer_role())[offset:offset + limit]
            else:
                users = User.objects.filter(role=Role.customer_role())[offset:offset + limit]
            user_serializer = UserSerializer(users, many=True)
            return JsonResponse(user_serializer.data, safe=False)
        elif self.method == 'POST':
            user_data = JSONParser().parse(self)
            try:
                user_firebase = auth.get_user(user_data['uid'])
                users = User.objects.filter(uid=user_firebase.uid)
                if users:
                    return JsonResponse(UserSerializer(users[0]).data, status=status.HTTP_200_OK, safe=False)
                else:
                    user = User.create(email=user_firebase.email, uid=user_firebase.uid, password=None,
                                       phone=user_firebase.phone_number, avatar_url=user_firebase.photo_url,
                                       name=user_firebase.display_name, role=Role.create(role_id=1, name="USER"))
                    user.save()
                    return JsonResponse({"user": UserSerializer(user), "token": user.token},
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
                user_access = User.objects.get(uid=payload['id'], is_active=True)

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
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            user_data = JSONParser().parse(self)
            user = User.objects.get(id=user_id)
            user.is_active = user_data['is_active']
            user.save()
            return HttpResponse(status=status.HTTP_204_NO_CONTENT)
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
            return JsonResponse({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
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

            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            offset, limit = parse_offset_limit(offset, limit)
            images = Image.objects.filter(user=user_id).order_by('-date_time')[offset:offset + limit]
            image_serializer = ImageSerializer(images, many=True)
            return JsonResponse(image_serializer.data, safe=False)
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
