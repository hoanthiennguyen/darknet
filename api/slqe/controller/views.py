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
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from pathlib import Path
from slqe.service.user_service import *

from slqe.service.image_service import *

from slqe.service.class_version_service import *

logger = logging.getLogger(__name__)


class SlqeApi(APIView):
    parser_classes = (MultiPartParser, FormParser,)

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
            version_name = self.GET.get('version_name')
            offset, limit = parse_offset_limit(offset, limit)
            versions = WeightVersion.objects.filter(class_version=class_id, version__icontains=version_name).order_by(
                '-created_date')
            total = len(versions)
            versions = versions[offset:offset + limit]
            weight_serializer = WeightSerializer(versions, many=True)
            return JsonResponse({"total": total, "data": weight_serializer.data}, safe=False)
        elif self.method == 'POST':
            dt = datetime.now()
            weight_obj = self.FILES['weight']
            loss_obj = self.FILES['loss']
            log_obj = self.FILES['log']
            if weight_obj and loss_obj and log_obj:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
                script_dir = Path(os.path.dirname(__file__))
                parent = script_dir.parent
                save_path = os.path.join(parent, "weights", str(payload["id"]), str(int(time.mktime(dt.timetuple()))))
                weight_name = "updated_weights.weights"
                loss_name = "chart.png"
                log_name = "train.log"
                Path(f"{save_path}").mkdir(parents=True, exist_ok=True)
                weight_complete_name = os.path.join(save_path, weight_name)
                loss_complete_name = os.path.join(save_path, loss_name)
                log_complete_name = os.path.join(save_path, log_name)

                # open read and write the weight into the server
                open(weight_complete_name, 'wb').write(weight_obj.file.read())
                # open read and write the log into the server
                open(log_complete_name, 'wb').write(log_obj.file.read())
                # open read and write the loss chart into the server
                open(loss_complete_name, 'wb').write(loss_obj.file.read())

                version = WeightVersion.objects.filter(class_version=class_id).order_by('-created_date').first()
                if version:
                    version = int(version.version) + 1
                else:
                    version = 1
                weight = WeightVersion.create(class_version=class_version, version=version,
                                              url=os.path.relpath(weight_complete_name),
                                              loss_function_path=os.path.relpath(loss_complete_name),
                                              log_path=os.path.relpath(log_complete_name)
                                              )
                weight.save()
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

