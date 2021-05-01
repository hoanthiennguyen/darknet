from django.conf.urls import url 
from slqe.controller.views import *
from slqe.controller.user_controller import UserController
from slqe.controller.image_controller import ImageController
from slqe.controller.class_version_controller import ClassVersionController
from slqe.controller.notification_controller import NotificationController

urlpatterns = [
    url(r'^users$', UserController.user_list),
    url(r'^users/(\w+)$', UserController.user_detail),
    url(r'^images$', ImageController.process_image),
    url(r'^users/(\w+)/images$', ImageController.user_images),
    url(r'^users/(\w+)/images/(\w+)$', ImageController.images_detail),
    url(r'^versions$', ClassVersionController.class_list),
    url(r'^versions/(\w+)$', ClassVersionController.class_detail),
    url(r'^versions/get-last-version', ClassVersionController.class_get_last_version),
    url(r'^versions/(\w+)/weights$', SlqeApi.weight_list),
    url(r'^versions/(\w+)/weights/(\w+)$', SlqeApi.weight_detail),
    url(r'^versions/(\w+)/weights/weight-get-last-version$', SlqeApi.weight_get_last_version),
    url(r'^users/(\w+)/notifications$', NotificationController.notification_list),
    url(r'^users/(\w+)/notifications/delete-all-read$', NotificationController.notification_delete_all_read),
    url(r'^users/(\w+)/notifications/(\w+)$', NotificationController.notification_detail),
    url(r'^users/(\w+)/notifications/count-unread$', NotificationController.notification_count_unread),
]
