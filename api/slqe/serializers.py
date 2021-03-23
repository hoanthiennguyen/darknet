from rest_framework import serializers
from slqe.models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'uid',
                  'password',
                  'phone',
                  'avatar_url',
                  'name',
                  'role',
                  'is_active')


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id',
                  'user',
                  'url',
                  'date_time',
                  'expression',
                  'latex',
                  'roots',
                  'success',
                  'message')
