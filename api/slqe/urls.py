from django.conf.urls import url 
from slqe.views import *
 
urlpatterns = [
    url(r'^users', SLQE_API.user_list),
    url(r'^users/{id}', SLQE_API.user_detail),
    url(r'^upload', SLQE_API.get_image)
]