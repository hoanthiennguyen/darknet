from rest_framework import serializers 
from slqe.models import *
 
 
class UserSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = User
        fields = ('id',
                  'email',
                  'phone',
                  'url',
                  'name',
                  'role')

class ImageSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Image
        fields = ('id',
                  'user',
                  'url')

class RoleSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Role
        fields = ('id',
                  'name')
