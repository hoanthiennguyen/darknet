from django.db import models
from django_mysql.models import ListCharField


# Create your models here.
class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    class Meta:
        db_table = 'role'


class User(models.Model):
    id = models.AutoField(primary_key=True)
    email = models.CharField(max_length=255, unique=True)
    uid = models.CharField(max_length=255, null=True)
    password = models.CharField(max_length=255, null=True)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255)
    avatar_url = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True, null=True)

    class Meta:
        db_table = 'user'


class Image(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    url = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    expression = models.CharField(max_length=255)
    latex = models.CharField(max_length=255)
    roots = ListCharField(
        base_field=models.CharField(max_length=255),
        size=10,
        max_length=(10 * 256)  # 6 * 10 character nominals, plus commas
    )

    class Meta:
        db_table = 'image'

    @classmethod
    def create(cls, user, url, date_time, expression, latex, roots):
        return cls(user=user, url=url + "_" + str(date_time), date_time=date_time, expression=expression,
                   latex=latex, roots=roots)


class ClassVersion(models.Model):
    version = models.CharField(max_length=255, primary_key=True)
    commit_hash = models.CharField(max_length=255)
    date_time = models.DateTimeField()

    class Meta:
        db_table = 'class_version'


class WeightVersion(models.Model):
    version = models.CharField(max_length=255, primary_key=True)
    url = models.CharField(max_length=255)
    date_time = models.DateTimeField()
    class_version = models.ForeignKey(ClassVersion, on_delete=models.CASCADE)

    class Meta:
        db_table = 'weight_version'
