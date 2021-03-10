
import PIL.Image
import os
from numpy import asarray
from slqe.custom_storage import MediaStorage
from django.http.response import *
from rest_framework.parsers import *
from rest_framework.views import *
import time
import base64
from slqe.models import *
from slqe.serializers import *
from rest_framework.decorators import api_view
from processor import algorithm
import cv2
import numpy as np
import boto3
# Create your views here.
# ------- User view -------------------


class SLQE_API(APIView):
    parser_classes = (MultiPartParser, FormParser, )
    @api_view(['GET', 'POST'])
    def user_list(request):
        if request.method == 'GET':
            users = User.objects.all()
            user_serializer = UserSerializer(users, many=True)
            return JsonResponse(user_serializer.data, safe=False)
            # 'safe=False' for objects serialization
        elif request.method == 'POST':
            user_data = JSONParser().parse(request)
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                user_serializer.save()
                return JsonResponse(user_serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
 
    @api_view(['GET', 'PUT', 'DELETE'])
    def user_detail(request, id):
        try: 
            user = User.objects.get(id=id)
            user_serializer = UserSerializer(user, many=True)
        except User.DoesNotExist: 
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'GET':
            return JsonResponse(user_serializer.data, safe=False)
        elif request.method == 'PUT':
            user_data = JSONParser().parse(request)
            user_serializer = UserSerializer(user, data=user_data)
            if user_serializer.is_valid():
                user_serializer.save()
                return JsonResponse(user_serializer.data, status=status.HTTP_204_NO_CONTENT)
            else:
                return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.method == 'DELETE':
            user.delete()
            return JsonResponse({'message': 'User was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)

# ------- Image view -------------------

    @api_view(['POST'])
    def upload_image(request, format=None):
        file_obj = request.FILES['file']
        try:
            image = PIL.Image.open(file_obj)
        except:
            return JsonResponse({"message": "An application require a image to reconigzation"}, status=HTTP_400_BAD_REQUEST)
        
        # parse numpy array and solve equation
        parsed_array = asarray(image)
        parsed_array = cv2.cvtColor(parsed_array, cv2.COLOR_RGB2BGR)

        expression, roots = algorithm.process(parsed_array)

        # upload image to s3
        # parse MD5 to origin file
        file_obj.seek(0, 0)
        # current_time = "_" + (round(time.time() * 1000))
        filename = file_obj.name
        s3 = boto3.resource('s3', aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY)
        bucket = s3.Bucket(settings.AWS_STORAGE_BUCKET_NAME)
        bucket.put_object(Key=filename, Body=file_obj)

        return JsonResponse({"expression": expression, "roots": roots}, status=status.HTTP_200_OK)