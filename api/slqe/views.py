import PIL.Image
from numpy import asarray

from django.http.response import *
from rest_framework.parsers import *
from rest_framework.views import *

from slqe.serializers import *
from rest_framework.decorators import api_view
from processor import algorithm
import cv2


# Create your views here.
# ------- User view -------------------


class SlqeApi(APIView):
    parser_classes = (MultiPartParser, FormParser,)

    @api_view(['GET', 'POST'])
    def user_list(self):
        if self.method == 'GET':
            users = User.objects.all()
            user_serializer = UserSerializer(users, many=True)
            return JsonResponse(user_serializer.data, safe=False)
            # 'safe=False' for objects serialization
        elif self.method == 'POST':
            user_data = JSONParser().parse(self)
            user_serializer = UserSerializer(data=user_data)
            if user_serializer.is_valid():
                user_serializer.save()
                return JsonResponse(user_serializer.data, status=status.HTTP_201_CREATED)
            return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
                return JsonResponse(user_serializer.data, status=status.HTTP_204_NO_CONTENT)
            else:
                return JsonResponse(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif self.method == 'DELETE':
            user.delete()
            return JsonResponse({'message': 'User was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)

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

    @api_view(['POST'])
    def save_image(self):
        image_data = JSONParser().parse(self)
        image_serializer = ImageSerializer(data=image_data)
        if image_serializer.is_valid():
            image_serializer.save()
            return JsonResponse(image_serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(image_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @api_view(['GET', 'DELETE'])
    def images_detail(self, user_id, image_id):
        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        try:
            image = Image.objects.get(id=image_id)
        except Image.DoesNotExist:
            return JsonResponse({'message': 'The image does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if image.user.id != user_id:
            return JsonResponse({"message": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)

        if self.method == 'GET':
            image_serializer = ImageSerializer(image)
            return JsonResponse(image_serializer.data, safe=False)
        elif self.method == 'DELETE':
            image.delete()
            return JsonResponse({'message': 'Image was deleted successfully!'}, status=status.HTTP_204_NO_CONTENT)

    @api_view(['GET'])
    def user_images(self, user_id):
        try:
            User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        image = Image.objects.filter(user=user_id)
        image_serializer = ImageSerializer(image, many=True)
        return JsonResponse(image_serializer.data, safe=False)
