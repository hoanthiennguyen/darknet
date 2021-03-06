from django.conf.urls import url 
from slqe.views import *
 
urlpatterns = [
    url(r'^users', SLQE_API.user_list),
    url(r'^users/{id}', SLQE_API.user_detail),
    url(r'^upload', SLQE_API.get_image),
    url(r'^images', SLQE_API.images_list),
    url(r'^images/{id}', SLQE_API.images_detail),
    url(r'^images/users/{id}', SLQE_API.get_images_by_user),

]
