from rest_framework import serializers
from slqe.models import *

from slqe.models import ClassVersion


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


class ImageSerializer(serializers.Serializer):
    def create(self, validated_data):
        serializers.ModelSerializer.create(validated_data)

    def update(self, instance, validated_data):
        serializers.ModelSerializer.update(validated_data)

    id = serializers.IntegerField()
    user = serializers.IntegerField(source='user.id')
    url = serializers.CharField()
    date_time = serializers.DateTimeField()
    expression = serializers.CharField()
    latex = serializers.CharField()
    roots = serializers.ListSerializer(child=serializers.CharField())
    success = serializers.BooleanField()
    message = serializers.CharField()


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassVersion
        fields = ('id',
                  'version',
                  'commit_hash',
                  'created_date',
                  )


class WeightSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightVersion
        fields = ('id',
                  'version',
                  'url',
                  'created_date',
                  'is_active',
                  'class_version',
                  )

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id',
                  'user',
                  'message',
                  'created_date',
                  'is_read',
                  'url',
                  'is_delete',
                  )

