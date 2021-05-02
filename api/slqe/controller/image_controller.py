from django.utils.datastructures import MultiValueDictKeyError
from numpy import asarray
from processor import algorithm
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.serializer.serializers import *
from slqe.service.class_version_service import *
from slqe.service.image_service import *
from slqe.service.image_service import ImageService
from slqe.service.user_service import *
from slqe.utils.jwt_utils import *

logger = logging.getLogger(__name__)


class ImageController(APIView):
    parser_classes = (MultiPartParser, FormParser)

    # ------- Image view -------------------

    @api_view(['POST'])
    def process_image(self):
        print(os.getcwd())
        file_obj = self.FILES.get('file')
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
            service = UserService()
            user = service.get_user_active(user_id)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        try:
            image_service = ImageService()
            image = image_service.get_image(image_id)
            if image.user.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        except Image.DoesNotExist:
            return JsonResponse({'message': 'The image does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            image_serializer = ImageSerializer(image)
            return JsonResponse(image_serializer.data, safe=False)
        elif self.method == 'DELETE':
            try:
                image_service = ImageService()
                image = image_service.find_image(image_id)
                if image.user.id != user.id:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)
                image_service.delete_image(image)
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except Image.DoesNotExist:
                return JsonResponse({'message': 'The image does not exist'}, status=status.HTTP_404_NOT_FOUND)

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
            service = UserService()
            user = service.get_user_active(user_id)
            if user_access.id != user.id:
                return HttpResponse(status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return JsonResponse({'message': 'The user does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except DecodeError:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            image_service = ImageService()
            total_image, images = image_service.get_images(user_id, limit, offset)
            image_serializer = ImageSerializer(images, many=True)
            return JsonResponse({"total": total_image, "data": image_serializer.data}, safe=False)
        elif self.method == 'POST':
            try:
                file_obj = self.FILES.get('file')
                save = "0"
                if self.POST and self.POST.get('save') and self.POST.get('save') == '1':
                    save = "1"
                image_service = ImageService()
                image_model = image_service.solve_equation(save, file_obj, user)
                image_serializer = ImageSerializer(image_model)
                return JsonResponse(image_serializer.data, status=status.HTTP_201_CREATED)
            except (MultiValueDictKeyError, UnidentifiedImageError):
                return JsonResponse({"message": "An application require a image to recognize"},
                                    status=status.HTTP_400_BAD_REQUEST)