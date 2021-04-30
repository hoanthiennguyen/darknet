from django.utils.datastructures import MultiValueDictKeyError
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
from firebase_admin.exceptions import FirebaseError
from numpy import asarray
from processor import algorithm
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


class ClassVersionController(APIView):
    parser_classes = (MultiPartParser, FormParser)

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
            version_name = self.GET.get('version_name')
            if version_name is None:
                return JsonResponse({"message": "Version name can not null"},
                                    status=status.HTTP_400_BAD_REQUEST)
            total, version = get_classes(limit, offset, version_name)
            class_serializer = ClassSerializer(version, many=True)
            return JsonResponse({"total": total, "data": class_serializer.data}, safe=False)
        elif self.method == 'POST':
            version_data = JSONParser().parse(self)
            class_serializer = ClassSerializer(data=version_data)
            if class_serializer.is_valid():
                class_serializer = create_class(class_serializer)
                return JsonResponse(class_serializer.data, status=status.HTTP_201_CREATED, safe=False)
            return JsonResponse(class_serializer.errors, status=status.HTTP_400_BAD_REQUEST)