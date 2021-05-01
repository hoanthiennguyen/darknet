import logging
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from slqe.service.weight_version_service import WeightVersionService
from slqe.service.class_version_service import ClassVersionService
from django.http.response import *

logger = logging.getLogger(__name__)


class WeightVersionController(APIView):
    parser_classes = (MultiPartParser, FormParser)

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
            class_version_service = ClassVersionService()
            class_version = class_version_service.get_class_by_id(class_id)
        except ClassVersion.DoesNotExist:
            return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            version_name = self.GET.get('version_name')
            offset, limit = parse_offset_limit(offset, limit)
            weight_version_service = WeightVersionService()
            total, versions = weight_version_service.get_weights(limit, offset, class_id, version_name)
            weight_serializer = WeightSerializer(versions, many=True)
            return JsonResponse({"total": total, "data": weight_serializer.data}, safe=False)
        elif self.method == 'POST':
            weight_obj = self.FILES.get('weight')
            loss_obj = self.FILES.get('loss')
            log_obj = self.FILES.get('log')
            if weight_obj and loss_obj and log_obj:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
                user_id = str(payload["id"])
                weight_version_service = WeightVersionService()
                weight_version_service.create_weight(weight_obj, loss_obj, log_obj, user_id, class_id, class_version)
                return HttpResponse(status=status.HTTP_201_CREATED)
            else:
                return JsonResponse({"message": "Please select weight, log and loss chart to create."},
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
            class_version_service = ClassVersionService()
            class_version_service.get_class_by_id(class_id)
        except ClassVersion.DoesNotExist:
            return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        if self.method == 'GET':
            try:
                weight_version_service = WeightVersionService()
                version = weight_version_service.get_weight_by_id(weight_id, class_id)
                weight_serializer = WeightSerializer(version)
                return JsonResponse(weight_serializer.data, safe=False)
            except WeightVersion.DoesNotExist:
                return JsonResponse({'message': 'The weight version does not exist'}, status=status.HTTP_404_NOT_FOUND)
        elif self.method == 'PUT':
            try:
                request_data = json.loads(self.body)
                url = request_data.get('url')
                is_active = request_data.get('is_active')
                weight_version_service = WeightVersionService()
                weight_version_service.update_weight(weight_id, url, is_active)

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
            class_version_service = ClassVersionService()
            class_version_service.get_class_by_id(class_id)
        except ClassVersion.DoesNotExist:
            return JsonResponse({'message': 'The class version does not exist'}, status=status.HTTP_404_NOT_FOUND)

        if self.method == 'GET':
            weight_version_service = WeightVersionService()
            version = weight_version_service.weight_get_last_version(class_id)
            if version:
                weight_serializer = WeightSerializer(version)
                return JsonResponse(weight_serializer.data, safe=False)
            return HttpResponse(status=status.HTTP_200_OK)
