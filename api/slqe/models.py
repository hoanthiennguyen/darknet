from django.db import models


# Create your models here.
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)


class User(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    email = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    avatar_url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
    date_time = models.DateTimeField(auto_now=True)

    @classmethod
    def create(cls, user, url):
        return cls(user=user, url=url)
