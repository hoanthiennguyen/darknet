from django.conf.urls import url 
from slqe.views import *
 
urlpatterns = [
    url(r'^users$', SlqeApi.user_list),
    url(r'^users/(\w+)$', SlqeApi.user_detail),
    url(r'^upload', SlqeApi.process_image),
    url(r'^users/(\w+)/images$', SlqeApi.user_images),
    url(r'^users/(\w+)/images/(\w+)', SlqeApi.images_detail),
]
