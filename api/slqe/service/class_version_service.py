import logging
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit

logger = logging.getLogger(__name__)


class ClassVersionService:
    pass

    def get_classes(self, limit, offset, version_name):
        offset, limit = parse_offset_limit(offset, limit)
        version = ClassVersion.objects.filter(version__icontains=version_name).order_by('-created_date')
        total = len(version)
        version = version[offset:offset + limit]
        return total, version

    def create_class(self, class_serializer):
        class_serializer.save()
        return class_serializer

    def get_class_by_id(self, class_id):
        image = ClassVersion.objects.get(pk=class_id)
        return image

    def class_get_last_version(self):
        version = ClassVersion.objects.order_by('-created_date').first()
        return version
