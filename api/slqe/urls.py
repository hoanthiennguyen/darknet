from django.conf.urls import url 
from slqe.views import *
 
urlpatterns = [
    url(r'^users$', SlqeApi.user_list),
    url(r'^users/(\w+)$', SlqeApi.user_detail),
    url(r'^upload', SlqeApi.get_image),
    url(r'^images', SlqeApi.images_list),
    url(r'^images/{id}', SlqeApi.images_detail),
    url(r'^images/users/{id}', SlqeApi.get_images_by_user),

]
