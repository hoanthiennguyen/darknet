from django.core.exceptions import ValidationError
from django.http.response import *
from firebase_admin.auth import UserNotFoundError
from firebase_admin.exceptions import FirebaseError
from rest_framework.decorators import api_view
from rest_framework.parsers import *
from rest_framework.views import *
from slqe.serializer.serializers import *
from slqe.service.class_version_service import *
from slqe.service.image_service import *
from slqe.service.user_service import *
from slqe.utils.jwt_utils import *

logger = logging.getLogger(__name__)


class UserController(APIView):
    parser_classes = (MultiPartParser, FormParser)

    @api_view(['GET', 'POST'])
    def user_list(self):
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
            name = self.GET.get('name')
            limit = self.GET.get('limit')
            offset = self.GET.get('offset')
            service = UserService()
            total_user, users = service.get_users(name, limit, offset)
            user_serializer = UserSerializer(users, many=True)
            return JsonResponse({"total": total_user, "data": user_serializer.data}, safe=False)
        elif self.method == 'POST':
            user_data = JSONParser().parse(self)
            try:
                uid = user_data['uid']
                service = UserService()
                user, is_active = service.login(uid)
                if is_active:
                    return JsonResponse({"user": UserSerializer(user).data, "token": user.token},
                                        status=status.HTTP_200_OK, safe=False)
                return JsonResponse({"user": UserSerializer(user).data, "token": user.token},
                                    status=status.HTTP_201_CREATED, safe=False)
            except UserNotFoundError:
                return HttpResponseBadRequest("User not found")
            except (ValueError, KeyError):
                return HttpResponseBadRequest("Error when retrieve user info: invalid uid")
            except FirebaseError:
                return HttpResponseServerError("Cannot retrieve user info from firebase")

    @api_view(['GET', 'PUT', 'DELETE'])
    def user_detail(self, user_id):
        # get token from header
        token = self.META.get('HTTP_AUTHORIZATION')
        # check authentication
        flag_verify = is_verified(token=token)
        if not flag_verify:
            return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
        if self.method == 'GET':
            try:
                # check authorization
                role = ("CUSTOMER", "ADMIN")
                flag_permission = is_permitted(token, role)
                if not flag_permission:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)

                payload = jwt.decode(token, settings.SECRET_KEY, algorithms='HS256')
                user_access = User.objects.get(id=payload['id'], is_active=True)
                service = UserService()
                user = service.get_user(user_id)
                if user_access.role.name == "CUSTOMER":
                    if user_access.id != user.id:
                        return HttpResponse(status=status.HTTP_403_FORBIDDEN)
                user_serializer = UserSerializer(user, many=False)
                return JsonResponse(user_serializer.data, safe=False)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except DecodeError:
                return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)

        elif self.method == 'PUT':
            try:
                # check authorization
                role = ("ADMIN")
                flag_permission = is_permitted(token, role)
                if not flag_permission:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)
                request_data = JSONParser().parse(self)
                service = UserService()
                service.update_user(user_id, request_data)
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except (ValidationError, KeyError):
                return HttpResponseBadRequest()
        elif self.method == 'DELETE':
            try:
                # check authorization
                role = ("ADMIN")
                flag_permission = is_permitted(token, role)
                if not flag_permission:
                    return HttpResponse(status=status.HTTP_403_FORBIDDEN)
                service = UserService()
                service.delete_user(user_id)
                return HttpResponse(status=status.HTTP_204_NO_CONTENT)
            except User.DoesNotExist:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)