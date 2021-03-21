import os
from datetime import datetime

import PIL.Image
import boto3
import cv2
from PIL import UnidentifiedImageError
from django.http.response import *
from numpy import asarray
from processor import algorithm
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.models import *
from slqe.serializers import *


# Create your views here.
# ------- User view -------------------


class SlqeApi(APIView):
    parser_classes = (MultiPartParser, FormParser,)

    @api_view(['GET', 'POST'])
    def user_list(self):
        if self.method == 'GET':
            users = User.objects.all()
            # users = users.filter(users.role.name == 'CUSTOMER')
            user_serializer = UserSerializer(users, many=True)
            return JsonResponse(user_serializer.data, safe=False)
            # 'safe=False' for objects serialization
        elif self.method == 'POST':
            user_data = JSONParser().parse(self)
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                user_serializer.save()
                return JsonResponse(user_serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(user_serializer.errors, status=status.HTTP_200_OK)

    @api_view(['GET', 'PUT', 'DELETE'])
    def user_detail(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            user_serializer = UserSerializer(user)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            return JsonResponse(user_serializer.data, safe=False)
        elif self.method == 'PUT':
            user_data = JSONParser().parse(self)
            user_serializer = UserSerializer(user, data=user_data)
            if user_serializer.is_valid():
                user_serializer.save()
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            else:
                return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif self.method == 'DELETE':
            if user.role.name == 'ADMIN':
                user.is_active = False
                user.save()
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            return JsonResponse({'message': 'Permission Denied!'}, status=status.HTTP_401_UNAUTHORIZED)

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
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            images = Image.objects.filter(user=user_id)
            image_serializer = ImageSerializer(images, many=True)
            return JsonResponse(image_serializer.data, safe=False)
        elif self.method == 'POST':
            # get file object
            file_obj = self.FILES['file']
            try:
                image = PIL.Image.open(file_obj)
            except UnidentifiedImageError:
                return JsonResponse({"message": "An application require a image to recognize"},
                                    status=status.HTTP_400_BAD_REQUEST)
            filename = file_obj.name
            now = datetime.datetime.now()
            # upload file to s3 storage
            file_obj.seek(0, 0)
            s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
            bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
            bucket.put_object(Key=filename + "_" + str(now), Body=file_obj)
            # location = boto3.client('s3').get_bucket_location(Bucket=settings.AWS_STORAGE_BUCKET_NAME)['LocationConstraint']
            url = "https://s3-%s.amazonaws.com/%s/%s" % (
            settings.AWS_LOCATION, settings.AWS_STORAGE_BUCKET_NAME, filename)
            # solver
            parsed_array = asarray(image)
            parsed_array = cv2.cvtColor(parsed_array, cv2.COLOR_RGB2BGR)

            valid, message, expression, latex, roots = algorithm.process(parsed_array)
            # insert data into database
            image = Image.create(user=user, url=url, date_time=now, expression=expression, latex=latex, roots=roots)
            image_serializer = ImageSerializer(image)
            image.save()
            return JsonResponse(image_serializer.data, status=status.HTTP_201_CREATED)
