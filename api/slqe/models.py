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
    url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)

class Image(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)