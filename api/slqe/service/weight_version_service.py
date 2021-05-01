import logging
from datetime import datetime

from django.http.response import *
from slqe.utils.jwt_utils import *
from slqe.serializer.serializers import *
from slqe.utils.utils import parse_offset_limit
from pathlib import Path

logger = logging.getLogger(__name__)


class WeightVersionService:
    pass

    def get_weights(self, limit, offset, class_id, version_name):
        offset, limit = parse_offset_limit(offset, limit)
        version = None
        if version_name:
            version = WeightVersion.objects.filter(class_version=class_id, version__icontains=version_name).order_by(
                '-created_date')
        else:
            version = WeightVersion.objects.filter(class_version=class_id).order_by('-created_date')
        total = len(version)
        version = version[offset:offset + limit]
        return total, version

    def create_weight(self, weight_obj, loss_obj, log_obj, user_id, class_id, class_version):
        dt = datetime.now()
        script_dir = Path(os.path.dirname(__file__))
        parent = script_dir.parent.parent
        save_path = os.path.join(parent, "weights", user_id, str(int(time.mktime(dt.timetuple()))))
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

    def get_weight_by_id(self, weight_id, class_id):
        weight = WeightVersion.objects.get(pk=weight_id, class_version=class_id)
        return weight

    def class_get_last_version():
        version = ClassVersion.objects.order_by('-created_date').first()
        return version

    def update_weight(self, weight_id, url, is_active):
        version = WeightVersion.objects.get(pk=weight_id)
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

    def weight_get_last_version(self, class_id):
        version = WeightVersion.objects.filter(class_version=class_id).order_by('-created_date').first()
        return version
